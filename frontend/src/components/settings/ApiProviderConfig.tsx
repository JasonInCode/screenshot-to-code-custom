import { ApiProvider, Settings } from "../../types";
import {
  API_PROVIDER_LABELS,
  PRESET_MODELS_BY_PROVIDER,
  DEFAULT_BASE_URLS,
} from "../../lib/models";
import { Input } from "../ui/input";
import { ModelCombobox } from "../ui/model-combobox";

interface Props {
  provider: ApiProvider;
  settings: Settings;
  setSettings: React.Dispatch<React.SetStateAction<Settings>>;
}

// 提供商配置字段名映射
const API_KEY_FIELD: Record<ApiProvider, keyof Settings> = {
  openai: "openAiApiKey",
  anthropic: "anthropicApiKey",
  gemini: "geminiApiKey",
};

const BASE_URL_FIELD: Record<ApiProvider, keyof Settings> = {
  openai: "openAiBaseURL",
  anthropic: "anthropicBaseURL",
  gemini: "geminiBaseURL",
};

export function ApiProviderConfig({ provider, settings, setSettings }: Props) {
  const label = API_PROVIDER_LABELS[provider];
  const apiKeyKey = API_KEY_FIELD[provider];
  const baseURLKey = BASE_URL_FIELD[provider];

  const apiKeyValue = (settings[apiKeyKey] as string | null) ?? "";
  const baseURLValue = (settings[baseURLKey] as string | null) ?? "";
  const defaultBaseUrl = DEFAULT_BASE_URLS[provider];
  const presetModels = PRESET_MODELS_BY_PROVIDER[provider];

  // 更新 API Key
  function handleApiKeyChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSettings((prev) => ({
      ...prev,
      [apiKeyKey]: e.target.value || null,
    }));
  }

  // 更新 Base URL
  function handleBaseURLChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSettings((prev) => ({
      ...prev,
      [baseURLKey]: e.target.value || null,
    }));
  }

  // 更新模型选择
  function handleModelChange(value: string) {
    setSettings((prev) => ({
      ...prev,
      codeGenerationModel: value,
    }));
  }

  return (
    <div className="space-y-4">
      {/* Base URL */}
      <div>
        <p className="text-sm font-medium">
          {label} Base URL <span className="text-muted-foreground">(optional)</span>
        </p>
        <p className="text-xs text-muted-foreground">
          Override the default API URL if using a proxy or self-hosted service
        </p>
        <Input
          placeholder={defaultBaseUrl}
          value={baseURLValue}
          onChange={handleBaseURLChange}
          className="mt-1.5"
        />
      </div>

      {/* API Key */}
      <div>
        <p className="text-sm font-medium">{label} API Key</p>
        <p className="text-xs text-muted-foreground">
          Keys are stored locally in your browser and never sent to third-party servers
        </p>
        <Input
          type="password"
          placeholder={`${label} API Key`}
          value={apiKeyValue}
          onChange={handleApiKeyChange}
          className="mt-1.5"
        />
      </div>

      {/* Model */}
      <div>
        <p className="text-sm font-medium">
          Model <span className="text-muted-foreground">(select or type custom)</span>
        </p>
        <p className="text-xs text-muted-foreground">
          Select a preset model or type a custom model ID
        </p>
        <div className="mt-1.5">
          <ModelCombobox
            value={settings.codeGenerationModel}
            onChange={handleModelChange}
            presetModels={presetModels}
          />
        </div>
      </div>
    </div>
  );
}