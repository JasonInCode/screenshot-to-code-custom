from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx

router = APIRouter()


class TestApiRequest(BaseModel):
    provider: str  # "openai" | "anthropic" | "gemini"
    apiKey: str
    baseURL: Optional[str] = None
    model: Optional[str] = None  # 用户配置的模型


class TestApiResponse(BaseModel):
    success: bool
    message: str
    model: Optional[str] = None
    supports_responses_api: Optional[bool] = None  # 是否支持 Responses API


# 默认 Base URL
DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
}

# 默认测试模型（当用户未配置模型时使用）
DEFAULT_TEST_MODELS = {
    "openai": "gpt-3.5-turbo",
    "anthropic": "claude-3-haiku-20240307",
    "gemini": "gemini-1.5-flash",
}


async def test_openai(api_key: str, base_url: str, model: str) -> TestApiResponse:
    """测试 OpenAI API 连通性，同时检测是否支持 Responses API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 🔍 先尝试 Responses API（/responses 端点）
        try:
            responses_response = await client.post(
                f"{base_url}/responses",
                headers=headers,
                json={
                    "model": model,
                    "input": [{"role": "user", "content": "Hi"}],
                    "max_output_tokens": 10,
                },
            )

            if responses_response.status_code == 200:
                data = responses_response.json()
                used_model = data.get("model", model)
                return TestApiResponse(
                    success=True,
                    message=f"Connection successful (Responses API)! Model: {used_model}",
                    model=used_model,
                    supports_responses_api=True,
                )
        except Exception:
            pass  # Responses API 不支持，继续尝试 Chat Completions

        # 🔍 再尝试 Chat Completions API（/chat/completions 端点）
        response = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10,
            },
        )

        if response.status_code == 200:
            data = response.json()
            used_model = data.get("model", model)
            return TestApiResponse(
                success=True,
                message=f"Connection successful (Chat Completions API)! Model: {used_model}",
                model=used_model,
                supports_responses_api=False,
            )
        else:
            error_data = response.json().get("error", {})
            error_message = error_data.get("message", response.text)
            return TestApiResponse(
                success=False,
                message=f"API error ({response.status_code}): {error_message}",
            )


async def test_anthropic(api_key: str, base_url: str, model: str) -> TestApiResponse:
    """测试 Anthropic API 连通性"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10,
            },
        )

        if response.status_code == 200:
            data = response.json()
            used_model = data.get("model", model)
            return TestApiResponse(
                success=True,
                message=f"Connection successful! Model: {used_model}",
                model=used_model,
            )
        else:
            error_data = response.json().get("error", {})
            error_message = error_data.get("message", response.text)
            return TestApiResponse(
                success=False,
                message=f"API error ({response.status_code}): {error_message}",
            )


async def test_gemini(api_key: str, base_url: str, model: str) -> TestApiResponse:
    """测试 Gemini API 连通性"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": "Hi"}]}],
                "generationConfig": {"maxOutputTokens": 10},
            },
        )

        if response.status_code == 200:
            data = response.json()
            return TestApiResponse(
                success=True,
                message=f"Connection successful! Model: {model}",
                model=model,
            )
        else:
            error_data = response.json().get("error", {})
            error_message = error_data.get("message", response.text)
            return TestApiResponse(
                success=False,
                message=f"API error ({response.status_code}): {error_message}",
            )


@router.post("/api/test-api", response_model=TestApiResponse)
async def test_api_connection(request: TestApiRequest):
    """测试 AI API 连通性"""
    provider = request.provider.lower()

    if provider not in DEFAULT_BASE_URLS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}. Must be one of: openai, anthropic, gemini",
        )

    if not request.apiKey:
        raise HTTPException(status_code=400, detail="API key is required")

    base_url = request.baseURL or DEFAULT_BASE_URLS[provider]
    # 优先使用用户配置的模型，否则使用默认测试模型
    model = request.model or DEFAULT_TEST_MODELS[provider]

    try:
        if provider == "openai":
            return await test_openai(request.apiKey, base_url, model)
        elif provider == "anthropic":
            return await test_anthropic(request.apiKey, base_url, model)
        elif provider == "gemini":
            return await test_gemini(request.apiKey, base_url, model)
    except httpx.TimeoutException:
        return TestApiResponse(
            success=False, message="Connection timeout (30s). Please check your network or API endpoint."
        )
    except Exception as e:
        return TestApiResponse(
            success=False, message=f"Connection failed: {str(e)}"
        )
