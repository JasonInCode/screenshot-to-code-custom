import asyncio
import json
import time
from typing import List, Literal, Union

import httpx
from openai import AsyncOpenAI

from image_generation.replicate import call_replicate


REPLICATE_BATCH_SIZE = 20


async def process_tasks(
    prompts: List[str],
    api_key: str,
    base_url: str | None,
    model: Literal["dalle3", "flux", "dashscope"],
    model_name: str = "dall-e-3",
) -> List[Union[str, None]]:
    start_time = time.time()
    results: list[str | BaseException | None]
    if model == "dashscope":
        # 📝 DashScope 限流策略：顺序请求，避免并发触发 429 RateQuota
        results = []
        for prompt in prompts:
            try:
                result = await generate_image_dashscope(prompt, api_key, base_url, model_name)
                results.append(result)
            except BaseException as e:
                results.append(e)
    elif model == "dalle3":
        tasks = [generate_image_dalle(prompt, api_key, base_url, model_name) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    else:
        results = []
        for i in range(0, len(prompts), REPLICATE_BATCH_SIZE):
            batch = prompts[i : i + REPLICATE_BATCH_SIZE]
            tasks = [generate_image_replicate(p, api_key) for p in batch]
            results.extend(await asyncio.gather(*tasks, return_exceptions=True))
    end_time = time.time()
    generation_time = end_time - start_time
    print(f"🖼️ [IMAGE_GEN] Image generation time: {generation_time:.2f} seconds, model={model_name}")

    processed_results: List[Union[str, None]] = []
    for result in results:
        if isinstance(result, BaseException):
            print(f"❌ [IMAGE_GEN] An exception occurred: {result}")
            processed_results.append(None)
        else:
            processed_results.append(result)

    return processed_results


async def generate_image_dashscope(
    prompt: str, api_key: str, base_url: str | None, model_name: str = "wan2.7-image-pro"
) -> Union[str, None]:
    """通过 DashScope 原生 API 生成图片

    TokenPlan/百炼的 OpenAI 兼容端点不支持 /images/generations，
    图片生成必须通过原生 API 端点:
      POST {base_domain}/api/v1/services/aigc/multimodal-generation/generation
    """
    # 从 base_url 提取域名基础部分
    # base_url 格式: https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
    # 原生 API: https://token-plan.cn-beijing.maas.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
    base_domain = base_url or "https://dashscope.aliyuncs.com"
    # 移除 /compatible-mode/v1 或 /v1 后缀
    for suffix in ("/compatible-mode/v1", "/compatible-mode", "/v1"):
        if base_domain.endswith(suffix):
            base_domain = base_domain[:-len(suffix)]
            break

    api_url = f"{base_domain}/api/v1/services/aigc/multimodal-generation/generation"

    # wan 系列用 "1K"/"2K"，qwen-image 系列用像素格式
    if model_name.startswith("wan"):
        size = "1K"
    else:
        size = "1024*1024"

    payload = {
        "model": model_name,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ]
        },
        "parameters": {
            "n": 1,
            "size": size,
        },
    }

    # 📝 调试日志
    masked_key = api_key[:8] + "..." + api_key[-4:] if api_key and len(api_key) > 12 else "(short key)"
    print(f"🖼️ [DASHSCOPE] api_url={api_url}, model={model_name}, api_key={masked_key}, size={size}")
    print(f"🖼️ [DASHSCOPE] prompt={prompt[:80]}...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 📝 429 限流重试：指数退避，最多 10 次
    max_retries = 10
    base_delay = 2  # 首次等待 2 秒

    async with httpx.AsyncClient(timeout=120) as client:
        for attempt in range(max_retries + 1):
            try:
                resp = await client.post(api_url, json=payload, headers=headers)

                # 429 限流：退避重试
                if resp.status_code == 429 and attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️ [DASHSCOPE] 429 限流，第 {attempt + 1} 次重试，等待 {delay} 秒...")
                    await asyncio.sleep(delay)
                    continue

                print(f"🖼️ [DASHSCOPE] 响应状态码: {resp.status_code}")

                if resp.status_code != 200:
                    print(f"❌ [DASHSCOPE] 请求失败: {resp.text[:300]}")
                    return None

                resp_data = resp.json()
                output = resp_data.get("output", {})
                choices = output.get("choices", [])

                if not choices:
                    print(f"❌ [DASHSCOPE] 响应中无 choices: {json.dumps(resp_data)[:300]}")
                    return None

                # 从 choices[0].message.content[0].image 提取 URL
                message = choices[0].get("message", {})
                content_list = message.get("content", [])

                for item in content_list:
                    image_url = item.get("image", "")
                    if image_url:
                        print(f"✅ [DASHSCOPE] 图片生成成功: {image_url[:100]}...")
                        return image_url

                print(f"❌ [DASHSCOPE] content 中无 image 字段: {json.dumps(content_list)[:300]}")
                return None

            except Exception as e:
                print(f"❌ [DASHSCOPE] 请求异常: {e}")
                return None

    # 重试耗尽仍未成功
    print(f"❌ [DASHSCOPE] 重试耗尽，429 限流未解除")
    return None


async def generate_image_dalle(
    prompt: str, api_key: str, base_url: str | None, model_name: str = "dall-e-3"
) -> Union[str, None]:
    # 📝 调试日志：打印图片生成请求详情
    masked_key = api_key[:8] + "..." + api_key[-4:] if api_key and len(api_key) > 12 else "(short key)"
    print(f"🖼️ [DALLE] base_url={base_url}, model_name={model_name}, api_key={masked_key}")
    print(f"🖼️ [DALLE] prompt={prompt[:80]}...")

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    # 仅 DALL-E 3 支持 quality/style 参数，其他 OpenAI 兼容模型不支持
    if model_name == "dall-e-3":
        print(f"🖼️ [DALLE] 使用 DALL-E 3 参数集 (quality=standard, style=natural)")
        res = await client.images.generate(
            model=model_name,
            quality="standard",
            style="natural",
            n=1,
            size="1024x1024",
            prompt=prompt,
        )
    else:
        print(f"🖼️ [DALLE] 使用基础参数集 (无 quality/style)")
        res = await client.images.generate(
            model=model_name,
            n=1,
            size="1024x1024",
            prompt=prompt,
        )
    await client.close()
    if not res.data:
        print(f"❌ [DALLE] 返回数据为空")
        return None
    print(f"✅ [DALLE] 成功，URL={res.data[0].url}")
    return res.data[0].url


async def generate_image_replicate(prompt: str, api_key: str) -> str:
    # We use Flux 2 Klein
    return await call_replicate(
        {
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "output_format": "png",
        },
        api_key,
    )
