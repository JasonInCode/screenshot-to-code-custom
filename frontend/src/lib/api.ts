import { ApiProvider } from "../types";

// 测试API连通性请求参数
export interface TestApiParams {
  provider: ApiProvider;
  apiKey: string;
  baseURL?: string | null;
  model?: string | null;
}

// 测试API连通性响应
export interface TestApiResult {
  success: boolean;
  message: string;
  model?: string | null;
  supports_responses_api?: boolean | null;  // 是否支持 Responses API
  supports_anthropic_images?: boolean | null;  // 是否支持 Anthropic 图片格式
}

// 测试AI API连通性
export async function testApiConnection(params: TestApiParams): Promise<TestApiResult> {
  const { provider, apiKey, baseURL, model } = params;

  const response = await fetch("/api/test-api", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      provider,
      apiKey,
      baseURL: baseURL || null,
      model: model || null,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}
