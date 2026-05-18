import { ApiProvider } from "../types";

// Keep in sync with backend (llm.py)
// Order here matches dropdown order
export enum CodeGenerationModel {
  CLAUDE_OPUS_4_6 = "claude-opus-4-6",
  CLAUDE_SONNET_4_6 = "claude-sonnet-4-6",
  CLAUDE_4_5_OPUS_2025_11_01 = "claude-opus-4-5-20251101",
  CLAUDE_4_5_SONNET_2025_09_29 = "claude-sonnet-4-5-20250929",
  GPT_5_2_CODEX_LOW = "gpt-5.2-codex (low thinking)",
  GPT_5_2_CODEX_MEDIUM = "gpt-5.2-codex (medium thinking)",
  GPT_5_2_CODEX_HIGH = "gpt-5.2-codex (high thinking)",
  GPT_5_2_CODEX_XHIGH = "gpt-5.2-codex (xhigh thinking)",
  GPT_5_3_CODEX_LOW = "gpt-5.3-codex (low thinking)",
  GPT_5_3_CODEX_MEDIUM = "gpt-5.3-codex (medium thinking)",
  GPT_5_3_CODEX_HIGH = "gpt-5.3-codex (high thinking)",
  GPT_5_3_CODEX_XHIGH = "gpt-5.3-codex (xhigh thinking)",
  GEMINI_3_FLASH_PREVIEW_HIGH = "gemini-3-flash-preview (high thinking)",
  GEMINI_3_FLASH_PREVIEW_MINIMAL = "gemini-3-flash-preview (minimal thinking)",
  GEMINI_3_1_PRO_PREVIEW_HIGH = "gemini-3.1-pro-preview (high thinking)",
  GEMINI_3_1_PRO_PREVIEW_MEDIUM = "gemini-3.1-pro-preview (medium thinking)",
  GEMINI_3_1_PRO_PREVIEW_LOW = "gemini-3.1-pro-preview (low thinking)",
}

// 已知预设模型的描述信息
// 类型使用 Record<string, ...> 以支持对自定义模型 ID 的查找（自定义模型不在字典中则返回 undefined）
export const CODE_GENERATION_MODEL_DESCRIPTIONS: Record<
  string,
  { name: string; inBeta: boolean }
> = {
  "gpt-5.2-codex (low thinking)": {
    name: "GPT 5.2 Codex (low)",
    inBeta: true,
  },
  "gpt-5.2-codex (medium thinking)": {
    name: "GPT 5.2 Codex (medium)",
    inBeta: true,
  },
  "gpt-5.2-codex (high thinking)": {
    name: "GPT 5.2 Codex (high)",
    inBeta: true,
  },
  "gpt-5.2-codex (xhigh thinking)": {
    name: "GPT 5.2 Codex (xhigh)",
    inBeta: true,
  },
  "gpt-5.3-codex (low thinking)": {
    name: "GPT 5.3 Codex (low)",
    inBeta: true,
  },
  "gpt-5.3-codex (medium thinking)": {
    name: "GPT 5.3 Codex (medium)",
    inBeta: true,
  },
  "gpt-5.3-codex (high thinking)": {
    name: "GPT 5.3 Codex (high)",
    inBeta: true,
  },
  "gpt-5.3-codex (xhigh thinking)": {
    name: "GPT 5.3 Codex (xhigh)",
    inBeta: true,
  },
  "claude-opus-4-5-20251101": { name: "Claude Opus 4.5", inBeta: false },
  "claude-opus-4-6": { name: "Claude Opus 4.6", inBeta: false },
  "claude-sonnet-4-6": { name: "Claude Sonnet 4.6", inBeta: false },
  "claude-sonnet-4-5-20250929": { name: "Claude Sonnet 4.5", inBeta: false },
  "gemini-3-flash-preview (high thinking)": {
    name: "Gemini 3 Flash (high)",
    inBeta: true,
  },
  "gemini-3-flash-preview (minimal thinking)": {
    name: "Gemini 3 Flash (minimal)",
    inBeta: true,
  },
  "gemini-3.1-pro-preview (high thinking)": {
    name: "Gemini 3.1 Pro (high)",
    inBeta: true,
  },
  "gemini-3.1-pro-preview (medium thinking)": {
    name: "Gemini 3.1 Pro (medium)",
    inBeta: true,
  },
  "gemini-3.1-pro-preview (low thinking)": {
    name: "Gemini 3.1 Pro (low)",
    inBeta: true,
  },
};

// API 提供商分组常量

export const OPENAI_PRESET_MODELS: string[] = [
  CodeGenerationModel.GPT_5_2_CODEX_LOW,
  CodeGenerationModel.GPT_5_2_CODEX_MEDIUM,
  CodeGenerationModel.GPT_5_2_CODEX_HIGH,
  CodeGenerationModel.GPT_5_2_CODEX_XHIGH,
  CodeGenerationModel.GPT_5_3_CODEX_LOW,
  CodeGenerationModel.GPT_5_3_CODEX_MEDIUM,
  CodeGenerationModel.GPT_5_3_CODEX_HIGH,
  CodeGenerationModel.GPT_5_3_CODEX_XHIGH,
];

export const ANTHROPIC_PRESET_MODELS: string[] = [
  CodeGenerationModel.CLAUDE_OPUS_4_6,
  CodeGenerationModel.CLAUDE_SONNET_4_6,
  CodeGenerationModel.CLAUDE_4_5_OPUS_2025_11_01,
  CodeGenerationModel.CLAUDE_4_5_SONNET_2025_09_29,
];

export const GEMINI_PRESET_MODELS: string[] = [
  CodeGenerationModel.GEMINI_3_FLASH_PREVIEW_HIGH,
  CodeGenerationModel.GEMINI_3_FLASH_PREVIEW_MINIMAL,
  CodeGenerationModel.GEMINI_3_1_PRO_PREVIEW_HIGH,
  CodeGenerationModel.GEMINI_3_1_PRO_PREVIEW_MEDIUM,
  CodeGenerationModel.GEMINI_3_1_PRO_PREVIEW_LOW,
];

export const PRESET_MODELS_BY_PROVIDER: Record<ApiProvider, string[]> = {
  openai: OPENAI_PRESET_MODELS,
  anthropic: ANTHROPIC_PRESET_MODELS,
  gemini: GEMINI_PRESET_MODELS,
};

// API 提供商显示名称
export const API_PROVIDER_LABELS: Record<ApiProvider, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  gemini: "Gemini",
};

export const DEFAULT_BASE_URLS: Record<ApiProvider, string> = {
  openai: "https://api.openai.com/v1",
  anthropic: "https://api.anthropic.com",
  gemini: "https://generativelanguage.googleapis.com",
};

// 获取模型显示名称：已知预设模型返回友好名称，自定义模型直接显示原始 ID
export function getModelDisplayName(modelValue: string): string {
  const desc = CODE_GENERATION_MODEL_DESCRIPTIONS[modelValue];
  if (desc) return desc.name;
  return modelValue; // 自定义模型直接显示原始 ID
}
