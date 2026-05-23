# pyright: reportUnknownVariableType=false
import copy
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from agent.providers.base import (
    EventSink,
    ExecutedToolCall,
    ProviderSession,
    ProviderTurn,
    StreamEvent,
)
from agent.providers.pricing import MODEL_PRICING
from agent.providers.token_usage import TokenUsage
from agent.state import ensure_str
from agent.tools import CanonicalToolDefinition, ToolCall, parse_json_arguments
from config import IS_DEBUG_ENABLED
from fs_logging.openai_turn_inputs import OpenAITurnInputLogger
from llm import Llm, get_openai_api_name, get_openai_reasoning_effort


def _convert_message_to_responses_input(
    message: ChatCompletionMessageParam,
) -> Dict[str, Any]:
    role = message.get("role", "user")
    content = message.get("content", "")

    if isinstance(content, str):
        return {"role": role, "content": content}

    parts: List[Dict[str, Any]] = []
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text":
                parts.append({"type": "input_text", "text": part.get("text", "")})
            elif part.get("type") == "image_url":
                image_url = part.get("image_url", {})
                parts.append(
                    {
                        "type": "input_image",
                        "image_url": image_url.get("url", ""),
                        "detail": image_url.get("detail", "high"),
                    }
                )

    return {"role": role, "content": parts}


def _get_event_attr(event: Any, key: str, default: Any = None) -> Any:
    if hasattr(event, key):
        return getattr(event, key)
    if isinstance(event, dict):
        return event.get(key, default)
    return default


def _copy_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(schema)


def _nullable_type(type_value: Any) -> Any:
    if isinstance(type_value, list):
        if "null" not in type_value:
            return [*type_value, "null"]
        return type_value
    if isinstance(type_value, str):
        return [type_value, "null"]
    return type_value


def _make_responses_schema_strict(schema: Dict[str, Any]) -> Dict[str, Any]:
    schema_copy: Dict[str, Any] = _copy_schema(schema)

    def transform(node: Dict[str, Any], in_object_property: bool = False) -> None:
        node_type = node.get("type")

        if node_type == "object":
            node["additionalProperties"] = False
            properties = node.get("properties") or {}
            if isinstance(properties, dict):
                node["required"] = list(properties.keys())
                for prop in properties.values():
                    if isinstance(prop, dict):
                        transform(prop, in_object_property=True)
            return

        if node_type == "array":
            if in_object_property:
                node["type"] = _nullable_type(node_type)
            items = node.get("items")
            if isinstance(items, dict):
                transform(items, in_object_property=False)
            return

        if in_object_property and node_type is not None:
            node["type"] = _nullable_type(node_type)

    transform(schema_copy, in_object_property=False)
    return schema_copy


def serialize_openai_tools(
    tools: List[CanonicalToolDefinition],
) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for tool in tools:
        schema = _make_responses_schema_strict(tool.parameters)
        serialized.append(
            {
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": schema,
                "strict": True,
            }
        )
    return serialized


def serialize_chat_completions_tools(
    tools: List[CanonicalToolDefinition],
) -> List[Dict[str, Any]]:
    """Chat Completions API 工具序列化（不做 Responses API 的 schema 修改）"""
    serialized: List[Dict[str, Any]] = []
    for tool in tools:
        serialized.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
        )
    return serialized
@dataclass
class OpenAIResponsesParseState:
    assistant_text: str = ""
    tool_calls: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    item_to_call_id: Dict[str, str] = field(default_factory=dict)
    output_items_by_index: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    saw_reasoning_summary_text_delta: bool = False
    last_emitted_reasoning_summary_part: str = ""
    turn_usage: TokenUsage | None = None


def _extract_openai_usage(response: Any) -> TokenUsage:
    """Extract unified token usage from an OpenAI Responses ``response.completed`` event.

    OpenAI includes cached tokens inside ``input_tokens``, so they are subtracted
    to get the non-cached input count.
    """
    usage = _get_event_attr(response, "usage")
    if usage is None:
        return TokenUsage()
    input_tokens = _get_event_attr(usage, "input_tokens", 0) or 0
    output_tokens = _get_event_attr(usage, "output_tokens", 0) or 0
    total_tokens = _get_event_attr(usage, "total_tokens", 0) or 0

    details = _get_event_attr(usage, "input_tokens_details") or {}
    cached_tokens = _get_event_attr(details, "cached_tokens", 0) or 0

    return TokenUsage(
        input=input_tokens - cached_tokens,
        output=output_tokens,
        cache_read=cached_tokens,
        cache_write=0,
        total=total_tokens,
    )


async def parse_event(
    event: Any,
    state: OpenAIResponsesParseState,
    on_event: EventSink,
) -> None:
    event_type = _get_event_attr(event, "type")
    if event_type in (
        "response.created",
        "response.completed",
        "response.done",
        "response.output_item.done",
    ):
        if event_type == "response.completed":
            response = _get_event_attr(event, "response")
            if response:
                state.turn_usage = _extract_openai_usage(response)
        if event_type == "response.output_item.done":
            output_index = _get_event_attr(event, "output_index")
            item = _get_event_attr(event, "item")
            if isinstance(output_index, int) and item:
                state.output_items_by_index[output_index] = item
        return

    if event_type == "response.output_text.delta":
        delta = _get_event_attr(event, "delta", "")
        if delta:
            state.assistant_text += delta
            await on_event(StreamEvent(type="assistant_delta", text=delta))
        return

    if event_type in (
        "response.reasoning_text.delta",
        "response.reasoning_summary_text.delta",
    ):
        delta = _get_event_attr(event, "delta", "")
        if delta:
            if event_type == "response.reasoning_summary_text.delta":
                state.saw_reasoning_summary_text_delta = True
            await on_event(StreamEvent(type="thinking_delta", text=delta))
        return

    if event_type in (
        "response.reasoning_summary_part.added",
        "response.reasoning_summary_part.done",
    ):
        if state.saw_reasoning_summary_text_delta:
            return
        part = _get_event_attr(event, "part") or {}
        text = _get_event_attr(part, "text", "")
        if text and text != state.last_emitted_reasoning_summary_part:
            state.last_emitted_reasoning_summary_part = text
            await on_event(StreamEvent(type="thinking_delta", text=text))
        return

    if event_type == "response.output_item.added":
        item = _get_event_attr(event, "item")
        item_type = _get_event_attr(item, "type") if item else None
        output_index = _get_event_attr(event, "output_index")
        if isinstance(output_index, int) and item:
            state.output_items_by_index.setdefault(output_index, item)

        if item and item_type in ("function_call", "custom_tool_call"):
            item_id = _get_event_attr(item, "id")
            call_id = _get_event_attr(item, "call_id") or item_id
            if item_id and call_id:
                state.item_to_call_id[item_id] = call_id
            if call_id:
                if item_id and item_id in state.tool_calls and item_id != call_id:
                    existing = state.tool_calls.pop(item_id)
                    state.tool_calls[call_id] = {
                        **existing,
                        "id": call_id,
                    }
                args_value = _get_event_attr(item, "arguments")
                if args_value is None and item_type == "custom_tool_call":
                    args_value = _get_event_attr(item, "input")
                state.tool_calls.setdefault(
                    call_id,
                    {
                        "id": call_id,
                        "name": _get_event_attr(item, "name"),
                        "arguments": args_value or "",
                    },
                )
                if args_value:
                    await on_event(
                        StreamEvent(
                            type="tool_call_delta",
                            tool_call_id=call_id,
                            tool_name=_get_event_attr(item, "name"),
                            tool_arguments=args_value,
                        )
                    )
        return

    if event_type in (
        "response.function_call_arguments.delta",
        "response.mcp_call_arguments.delta",
        "response.custom_tool_call_input.delta",
    ):
        item_id = _get_event_attr(event, "item_id")
        call_id = _get_event_attr(event, "call_id")
        if call_id and item_id:
            state.item_to_call_id[item_id] = call_id
        if not call_id:
            call_id = state.item_to_call_id.get(item_id) if item_id else None
        if not call_id and item_id:
            call_id = item_id
        if not call_id:
            return

        entry = state.tool_calls.setdefault(
            call_id,
            {
                "id": call_id,
                "name": _get_event_attr(event, "name"),
                "arguments": "",
            },
        )
        delta_value = _get_event_attr(event, "delta")
        if delta_value is None:
            delta_value = _get_event_attr(event, "input")
        entry["arguments"] += ensure_str(delta_value)

        await on_event(
            StreamEvent(
                type="tool_call_delta",
                tool_call_id=call_id,
                tool_name=entry.get("name"),
                tool_arguments=entry.get("arguments"),
            )
        )
        return

    if event_type not in (
        "response.function_call_arguments.done",
        "response.mcp_call_arguments.done",
        "response.custom_tool_call_input.done",
    ):
        return

    item_id = _get_event_attr(event, "item_id")
    call_id = _get_event_attr(event, "call_id")
    if call_id and item_id:
        state.item_to_call_id[item_id] = call_id
    if not call_id:
        call_id = state.item_to_call_id.get(item_id) if item_id else None
    if not call_id and item_id:
        call_id = item_id
    if not call_id:
        return

    entry = state.tool_calls.setdefault(
        call_id,
        {
            "id": call_id,
            "name": _get_event_attr(event, "name"),
            "arguments": "",
        },
    )
    final_value = _get_event_attr(event, "arguments")
    if final_value is None:
        final_value = _get_event_attr(event, "input")
    if final_value is None:
        final_value = entry["arguments"]
    entry["arguments"] = final_value
    if _get_event_attr(event, "name"):
        entry["name"] = _get_event_attr(event, "name")

    await on_event(
        StreamEvent(
            type="tool_call_delta",
            tool_call_id=call_id,
            tool_name=entry.get("name"),
            tool_arguments=entry.get("arguments"),
        )
    )

    output_index = _get_event_attr(event, "output_index")
    if (
        item_id
        and isinstance(output_index, int)
        and isinstance(state.output_items_by_index.get(output_index), dict)
    ):
        state.output_items_by_index[output_index] = {
            **state.output_items_by_index[output_index],
            "arguments": entry["arguments"],
            "call_id": call_id,
            "name": entry.get("name"),
        }


def _build_provider_turn(state: OpenAIResponsesParseState) -> ProviderTurn:
    output_items = [
        state.output_items_by_index[idx]
        for idx in sorted(state.output_items_by_index.keys())
        if state.output_items_by_index.get(idx)
    ]

    tool_items = [
        item
        for item in output_items
        if isinstance(item, dict)
        and item.get("type") in ("function_call", "custom_tool_call")
    ]

    tool_calls: List[ToolCall] = []
    if tool_items:
        for item in tool_items:
            raw_args = item.get("arguments")
            if raw_args is None and item.get("type") == "custom_tool_call":
                raw_args = item.get("input")
            args, error = parse_json_arguments(raw_args)
            if error:
                args = {"INVALID_JSON": ensure_str(raw_args)}
            call_id = item.get("call_id") or item.get("id")
            tool_calls.append(
                ToolCall(
                    id=call_id or f"call-{uuid.uuid4().hex[:6]}",
                    name=item.get("name") or "unknown_tool",
                    arguments=args,
                )
            )
    else:
        for entry in state.tool_calls.values():
            args, error = parse_json_arguments(entry.get("arguments"))
            if error:
                args = {"INVALID_JSON": ensure_str(entry.get("arguments"))}
            call_id = entry.get("id") or entry.get("call_id")
            tool_calls.append(
                ToolCall(
                    id=call_id or f"call-{uuid.uuid4().hex[:6]}",
                    name=entry.get("name") or "unknown_tool",
                    arguments=args,
                )
            )

    assistant_turn: List[Dict[str, Any]] = output_items if tool_calls else []

    return ProviderTurn(
        assistant_text=state.assistant_text,
        tool_calls=tool_calls,
        assistant_turn=assistant_turn,
    )


class OpenAIProviderSession(ProviderSession):
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str | Llm,
        prompt_messages: List[ChatCompletionMessageParam],
        tools: List[Dict[str, Any]],
        use_chat_completions: bool = False,
    ):
        self._client = client
        self._model = model
        self._tools = tools
        self._use_chat_completions = use_chat_completions
        self._total_usage = TokenUsage()
        self._turn_input_logger = OpenAITurnInputLogger(
            model,
            enabled=IS_DEBUG_ENABLED,
        )
        self._input_items: List[Dict[str, Any]] = [
            _convert_message_to_responses_input(message) for message in prompt_messages
        ]
        # Chat Completions API 使用原始消息格式
        self._chat_messages: List[ChatCompletionMessageParam] = list(prompt_messages)

    async def _stream_chat_completions(self, on_event: EventSink) -> ProviderTurn:
        """使用 Chat Completions API（适用于 MiniMax 等第三方服务）"""
        model_name = self._model if isinstance(self._model, str) else get_openai_api_name(self._model)

        # 工具已经是 Chat Completions 格式，直接使用
        chat_tools = self._tools

        params: Dict[str, Any] = {
            "model": model_name,
            "messages": self._chat_messages,
            "stream": True,
            "max_tokens": 16000,
        }
        if chat_tools:
            params["tools"] = chat_tools
            params["tool_choice"] = "auto"

        # 调试日志：打印请求信息
        print(f"[DEBUG] Using Chat Completions API")
        print(f"[DEBUG] Base URL: {self._client.base_url}")
        print(f"[DEBUG] Model: {model_name}")
        print(f"[DEBUG] Messages count: {len(self._chat_messages)}")
        print(f"[DEBUG] Tools count: {len(chat_tools)}")

        self._turn_input_logger.record_turn_input(
            self._chat_messages,
            request_payload=params,
        )

        assistant_text = ""
        tool_calls: List[ToolCall] = []
        tool_call_chunks: Dict[int, Dict[str, Any]] = {}

        stream = await self._client.chat.completions.create(**params)
        async for chunk in stream:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            # 处理文本内容
            if delta.content:
                assistant_text += delta.content
                await on_event(StreamEvent(type="assistant_delta", text=delta.content))

            # 处理工具调用
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_call_chunks:
                        tool_call_chunks[idx] = {
                            "id": tc.id or "",
                            "name": tc.function.name if tc.function else "",
                            "arguments": "",
                        }
                    if tc.id:
                        tool_call_chunks[idx]["id"] = tc.id
                    if tc.function and tc.function.name:
                        tool_call_chunks[idx]["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        tool_call_chunks[idx]["arguments"] += tc.function.arguments

            # 只在流结束时处理工具调用（finish_reason 不为 None 表示流结束）
            if choice.finish_reason is not None and tool_call_chunks:
                print(f"[DEBUG] Processing {len(tool_call_chunks)} tool calls, finish_reason={choice.finish_reason}")
                for idx in sorted(tool_call_chunks.keys()):
                    tc_data = tool_call_chunks[idx]
                    print(f"[DEBUG] Tool call {idx}: name={tc_data['name']}, args_length={len(tc_data['arguments'])}")
                    print(f"[DEBUG] Raw args: {tc_data['arguments'][:500]}")
                    args, error = parse_json_arguments(tc_data["arguments"])
                    if error:
                        print(f"[DEBUG] ❌ JSON parse error: {error}")
                        args = {"INVALID_JSON": tc_data["arguments"]}
                    else:
                        print(f"[DEBUG] ✅ Parsed args keys: {list(args.keys())}")
                        if "content" in args:
                            print(f"[DEBUG] Content length: {len(str(args['content']))}")
                    # 始终生成新的唯一 ID，避免 MiniMax 返回重复 ID 的问题
                    unique_id = f"call-{uuid.uuid4().hex[:12]}"
                    tool_calls.append(ToolCall(
                        id=unique_id,
                        name=tc_data["name"] or "unknown_tool",
                        arguments=args,
                    ))

        # 更新消息历史
        assistant_message: ChatCompletionMessageParam = {
            "role": "assistant",
            "content": assistant_text,
        }
        if tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}
                }
                for tc in tool_calls
            ]
        self._chat_messages.append(assistant_message)

        return ProviderTurn(
            assistant_text=assistant_text,
            tool_calls=tool_calls,
            assistant_turn=[assistant_message] if tool_calls else [],
        )

    async def _stream_responses(self, on_event: EventSink) -> ProviderTurn:
        """使用 Responses API（适用于 OpenAI 官方模型）"""
        model_name = self._model if isinstance(self._model, str) else get_openai_api_name(self._model)
        params: Dict[str, Any] = {
            "model": model_name,
            "input": self._input_items,
            "tools": self._tools,
            "tool_choice": "auto",
            "stream": True,
            "max_output_tokens": 50000,
        }
        if model_name == "gpt-5.4-2026-03-05":
            params["prompt_cache_retention"] = "24h"
        if isinstance(self._model, Llm):
            reasoning_effort = get_openai_reasoning_effort(self._model)
            if reasoning_effort:
                params["reasoning"] = {"effort": reasoning_effort, "summary": "auto"}

        self._turn_input_logger.record_turn_input(
            self._input_items,
            request_payload=params,
        )

        state = OpenAIResponsesParseState()
        stream = await self._client.responses.create(**params)  # type: ignore
        async for event in stream:  # type: ignore
            await parse_event(event, state, on_event)

        if state.turn_usage is not None:
            self._turn_input_logger.record_turn_usage(state.turn_usage)
            self._total_usage.accumulate(state.turn_usage)

        return _build_provider_turn(state)

    async def stream_turn(self, on_event: EventSink) -> ProviderTurn:
        if self._use_chat_completions:
            return await self._stream_chat_completions(on_event)
        else:
            return await self._stream_responses(on_event)

    def append_tool_results(
        self,
        turn: ProviderTurn,
        executed_tool_calls: list[ExecutedToolCall],
    ) -> None:
        if self._use_chat_completions:
            # Chat Completions API 格式
            for executed in executed_tool_calls:
                self._chat_messages.append({
                    "role": "tool",
                    "tool_call_id": executed.tool_call.id,
                    "content": json.dumps(executed.result.result),
                })
        else:
            # Responses API 格式
            assistant_output_items = turn.assistant_turn or []
            if assistant_output_items:
                self._input_items.extend(assistant_output_items)

            tool_output_items: List[Dict[str, Any]] = []
            for executed in executed_tool_calls:
                tool_output_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": executed.tool_call.id,
                        "output": json.dumps(executed.result.result),
                    }
                )
            self._input_items.extend(tool_output_items)

    async def close(self) -> None:
        u = self._total_usage
        model_name = self._model if isinstance(self._model, str) else get_openai_api_name(self._model)
        pricing = MODEL_PRICING.get(model_name)
        cost_str = f" cost=${u.cost(pricing):.4f}" if pricing else ""
        cache_hit_rate_str = f" cache_hit_rate={u.cache_hit_rate_percent():.2f}%"
        print(
            f"[TOKEN USAGE] provider=openai model={model_name} | "
            f"input={u.input} output={u.output} "
            f"cache_read={u.cache_read} cache_write={u.cache_write} "
            f"total={u.total}{cache_hit_rate_str}{cost_str}"
        )
        report_path = self._turn_input_logger.write_html_report()
        if report_path:
            print(f"[OPENAI TURN INPUT] HTML report: {report_path}")
        await self._client.close()
