from typing import Optional

from anthropic import AsyncAnthropic
from google import genai
from google.genai import types
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from agent.providers.anthropic import AnthropicProviderSession, serialize_anthropic_tools
from agent.providers.base import ProviderSession
from agent.providers.gemini import GeminiProviderSession, serialize_gemini_tools
from agent.providers.openai import OpenAIProviderSession, serialize_chat_completions_tools, serialize_openai_tools
from agent.tools import canonical_tool_definitions
from llm import ANTHROPIC_MODELS, GEMINI_MODELS, OPENAI_MODELS, Llm


def create_provider_session(
    model: str | Llm,
    prompt_messages: list[ChatCompletionMessageParam],
    should_generate_images: bool,
    openai_api_key: Optional[str],
    openai_base_url: Optional[str],
    anthropic_api_key: Optional[str],
    anthropic_base_url: Optional[str],
    gemini_api_key: Optional[str],
    gemini_base_url: Optional[str],
    selected_api_provider: str | None = None,
    supports_responses_api: bool | None = None,
    supports_anthropic_images: bool | None = None,
    has_option_codes: bool = False,
) -> ProviderSession:
    canonical_tools = canonical_tool_definitions(
        image_generation_enabled=should_generate_images,
        has_option_codes=has_option_codes,
    )

    # 自定义模型字符串：根据 selected_api_provider 路由到对应 provider
    if isinstance(model, str):
        provider = selected_api_provider or "openai"
        if provider == "openai":
            if not openai_api_key:
                raise Exception("OpenAI API key is missing.")
            client = AsyncOpenAI(api_key=openai_api_key, base_url=openai_base_url)

            # 🔍 根据 API 兼容性检测结果决定使用哪种 API
            # supports_responses_api=True  → 使用 Responses API
            # supports_responses_api=False 或 None → 使用 Chat Completions API
            use_chat_completions = supports_responses_api is not True
            if use_chat_completions:
                tools = serialize_chat_completions_tools(canonical_tools)
            else:
                tools = serialize_openai_tools(canonical_tools)

            return OpenAIProviderSession(
                client=client,
                model=model,
                prompt_messages=prompt_messages,
                tools=tools,
                use_chat_completions=use_chat_completions,
            )
        if provider == "anthropic":
            if not anthropic_api_key:
                raise Exception("Anthropic API key is missing.")
            client = AsyncAnthropic(api_key=anthropic_api_key, base_url=anthropic_base_url)
            # 🔍 通过 base URL 检测是否是官方 Anthropic API
            # 官方 API 支持 eager_input_streaming 等特有字段
            is_official_anthropic = not anthropic_base_url or "api.anthropic.com" in (anthropic_base_url or "")
            return AnthropicProviderSession(
                client=client,
                model=model,
                prompt_messages=prompt_messages,
                tools=serialize_anthropic_tools(canonical_tools, include_eager_streaming=is_official_anthropic),
                supports_anthropic_images=True,  # Anthropic 兼容接口始终使用原生图片格式
            )
        if provider == "gemini":
            if not gemini_api_key:
                raise Exception("Gemini API key is missing.")
            http_options = None
            if gemini_base_url:
                http_options = types.HttpOptions(base_url=gemini_base_url)
            client = genai.Client(api_key=gemini_api_key, http_options=http_options)
            return GeminiProviderSession(
                client=client,
                model=model,
                prompt_messages=prompt_messages,
                tools=serialize_gemini_tools(canonical_tools),
            )
        raise ValueError(f"Unknown provider: {provider} for custom model: {model}")

    # 已知 Llm enum 值：按原逻辑路由
    if model in OPENAI_MODELS:
        if not openai_api_key:
            raise Exception("OpenAI API key is missing.")

        client = AsyncOpenAI(api_key=openai_api_key, base_url=openai_base_url)
        return OpenAIProviderSession(
            client=client,
            model=model,
            prompt_messages=prompt_messages,
            tools=serialize_openai_tools(canonical_tools),
        )

    if model in ANTHROPIC_MODELS:
        if not anthropic_api_key:
            raise Exception("Anthropic API key is missing.")

        client = AsyncAnthropic(api_key=anthropic_api_key, base_url=anthropic_base_url)
        return AnthropicProviderSession(
            client=client,
            model=model,
            prompt_messages=prompt_messages,
            tools=serialize_anthropic_tools(canonical_tools),
        )

    if model in GEMINI_MODELS:
        if not gemini_api_key:
            raise Exception("Gemini API key is missing.")

        http_options = None
        if gemini_base_url:
            http_options = types.HttpOptions(base_url=gemini_base_url)
        client = genai.Client(api_key=gemini_api_key, http_options=http_options)
        return GeminiProviderSession(
            client=client,
            model=model,
            prompt_messages=prompt_messages,
            tools=serialize_gemini_tools(canonical_tools),
        )

    raise ValueError(f"Unsupported model: {model.value}")
