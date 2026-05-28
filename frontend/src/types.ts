import { Stack } from "./lib/stacks";

export type ApiProvider = "openai" | "anthropic" | "gemini";
export type ImageGenerationProvider = "openai" | "dashscope";

export enum EditorTheme {
  ESPRESSO = "espresso",
  COBALT = "cobalt",
}

export enum AppTheme {
  SYSTEM = "system",
  LIGHT = "light",
  DARK = "dark",
}

export interface Settings {
  selectedApiProvider: ApiProvider;
  openAiApiKey: string | null;
  openAiBaseURL: string | null;
  anthropicApiKey: string | null;
  anthropicBaseURL: string | null;
  geminiApiKey: string | null;
  geminiBaseURL: string | null;
  screenshotOneApiKey: string | null;
  isImageGenerationEnabled: boolean;
  // 图片生成自定义配置
  imageGenerationBaseUrl: string | null;
  imageGenerationApiKey: string | null;
  imageGenerationModel: string | null;
  imageGenerationProvider: ImageGenerationProvider;
  editorTheme: EditorTheme;
  generatedCodeConfig: Stack;
  codeGenerationModel: string;
  selectedDesignSystemId: string | null;
  // API 兼容性检测结果（测试时自动填充）
  supportsResponsesApi: boolean | null;
  supportsAnthropicImages: boolean | null;  // 是否支持 Anthropic 图片格式
  // 生成的 options 数量
  numVariants: number;
  // Only relevant for hosted version
  isTermOfServiceAccepted: boolean;
}

export interface DesignSystem {
  id: string;
  name: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

export enum AppState {
  INITIAL = "INITIAL",
  CODING = "CODING",
  CODE_READY = "CODE_READY",
}

export enum ScreenRecorderState {
  INITIAL = "initial",
  RECORDING = "recording",
  FINISHED = "finished",
}

export type PromptMessageRole = "user" | "assistant";
export type PromptAssetType = "image" | "video";

export interface PromptAsset {
  id: string;
  type: PromptAssetType;
  dataUrl: string;
}

export interface PromptContent {
  text: string;
  images: string[]; // Array of data URLs
  videos?: string[]; // Array of data URLs
  selectedElementHtml?: string; // Raw HTML of selected element (for display only)
}

export interface PromptHistoryMessage {
  role: PromptMessageRole;
  text: string;
  images: string[];
  videos: string[];
}

export interface CodeGenerationParams {
  generationType: "create" | "update";
  inputMode: "image" | "video" | "text";
  prompt: PromptContent;
  history?: PromptHistoryMessage[];
  fileState?: {
    path: string;
    content: string;
  };
  optionCodes?: string[];
  retryVariantIndex?: number;
  sessionId?: string;
}

export type FullGenerationSettings = CodeGenerationParams &
  Settings & {
    designSystem?: string | null;
  };
