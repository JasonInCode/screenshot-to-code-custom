import React, { useState, useEffect } from "react";
import { AppTheme, ApiProvider, EditorTheme, Settings } from "../../types";
import { capitalize } from "../../lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "../ui/select";
import { Input } from "../ui/input";
import { Switch } from "../ui/switch";
import { Button } from "../ui/button";
import { ApiProviderSelector } from "./ApiProviderSelector";
import { ApiProviderConfig } from "./ApiProviderConfig";
import { testApiConnection, TestApiResult } from "../../lib/api";

interface Props {
  settings: Settings;
  setSettings: React.Dispatch<React.SetStateAction<Settings>>;
  appTheme: AppTheme;
  setAppTheme: React.Dispatch<React.SetStateAction<AppTheme>>;
}

function SettingsTab({ settings, setSettings, appTheme, setAppTheme }: Props) {
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<TestApiResult | null>(null);

  // 切换 provider 时清除测试结果
  useEffect(() => {
    setTestResult(null);
  }, [settings.selectedApiProvider]);

  const handleThemeChange = (theme: EditorTheme) => {
    setSettings((s) => ({
      ...s,
      editorTheme: theme,
    }));
  };

  // 获取当前选中 provider 的 API Key 和 Base URL
  const getCurrentProviderConfig = () => {
    const provider = settings.selectedApiProvider;
    // 字段名映射（注意 openAi 是大写 A）
    const apiKeyMap: Record<ApiProvider, keyof Settings> = {
      openai: "openAiApiKey",
      anthropic: "anthropicApiKey",
      gemini: "geminiApiKey",
    };
    const baseURLMap: Record<ApiProvider, keyof Settings> = {
      openai: "openAiBaseURL",
      anthropic: "anthropicBaseURL",
      gemini: "geminiBaseURL",
    };
    return {
      apiKey: (settings[apiKeyMap[provider]] as string) || "",
      baseURL: (settings[baseURLMap[provider]] as string) || null,
    };
  };

  // 测试API连通性
  const handleTestApi = async () => {
    const { apiKey, baseURL } = getCurrentProviderConfig();

    if (!apiKey) {
      setTestResult({
        success: false,
        message: "Please enter an API key first",
      });
      return;
    }

    setTestLoading(true);
    setTestResult(null);

    try {
      const result = await testApiConnection({
        provider: settings.selectedApiProvider,
        apiKey,
        baseURL,
        model: settings.codeGenerationModel || null,
      });
      setTestResult(result);

      // 🔍 测试成功时，保存 API 兼容性信息
      if (result.success) {
        setSettings((s) => ({
          ...s,
          supportsResponsesApi: result.supports_responses_api ?? null,
          supportsAnthropicImages: result.supports_anthropic_images ?? null,
        }));
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : "Unknown error occurred",
      });
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="px-4 py-4 lg:px-6 lg:py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            Settings
          </h1>
        </div>

        <div className="mx-auto max-w-lg space-y-6">
          {/* Theme */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                Theme
              </h2>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-zinc-700">
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <span className="text-sm text-gray-700 dark:text-zinc-300">
                    App Theme
                  </span>
                  <p className="mt-0.5 text-xs text-gray-500 dark:text-zinc-400">
                    System default, with optional light/dark override
                  </p>
                </div>
                <Select
                  name="app-theme"
                  value={appTheme}
                  onValueChange={(value) => setAppTheme(value as AppTheme)}
                >
                  <SelectTrigger className="w-[140px]">
                    {capitalize(appTheme)}
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={AppTheme.SYSTEM}>System</SelectItem>
                    <SelectItem value={AppTheme.LIGHT}>Light</SelectItem>
                    <SelectItem value={AppTheme.DARK}>Dark</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <span className="text-sm text-gray-700 dark:text-zinc-300">
                    Code Editor Theme
                  </span>
                  <p className="mt-0.5 text-xs text-gray-500 dark:text-zinc-400">
                    Requires page refresh to update
                  </p>
                </div>
                <Select
                  name="editor-theme"
                  value={settings.editorTheme}
                  onValueChange={(value) =>
                    handleThemeChange(value as EditorTheme)
                  }
                >
                  <SelectTrigger className="w-[140px]">
                    <span className="notranslate" translate="no">
                      {capitalize(settings.editorTheme)}
                    </span>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cobalt">
                      <span className="notranslate" translate="no">Cobalt</span>
                    </SelectItem>
                    <SelectItem value="espresso">
                      <span className="notranslate" translate="no">Espresso</span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* API Keys */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                API Keys
              </h2>
              <Button
                variant="outline"
                size="sm"
                onClick={handleTestApi}
                disabled={testLoading}
                className="h-7 px-3 text-xs"
              >
                {testLoading ? (
                  <>
                    <svg
                      className="mr-1.5 h-3 w-3 animate-spin"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Testing...
                  </>
                ) : (
                  "Test"
                )}
              </Button>
            </div>
            {testResult && (
              <div
                className={`mx-4 mt-3 rounded-md px-3 py-2 text-xs ${
                  testResult.success
                    ? "bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
                    : "bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400"
                }`}
              >
                {testResult.message}
              </div>
            )}
            <div className="p-4">
              <ApiProviderSelector
                value={settings.selectedApiProvider}
                onChange={(provider: ApiProvider) =>
                  setSettings((s) => ({ ...s, selectedApiProvider: provider }))
                }
              />
              <div className="border-t border-dashed border-gray-200 dark:border-zinc-600 mt-3 pt-4">
                <ApiProviderConfig
                  provider={settings.selectedApiProvider}
                  settings={settings}
                  setSettings={setSettings}
                />
              </div>
            </div>
          </div>

          {/* Image Generation */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                Image Generation
              </h2>
            </div>
            <div className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-700 dark:text-zinc-300">
                    Placeholder Images
                  </p>
                  <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                    Generate placeholder images, disable to save costs
                  </p>
                </div>
                <Switch
                  id="image-generation"
                  checked={settings.isImageGenerationEnabled}
                  onCheckedChange={() =>
                    setSettings((s) => ({
                      ...s,
                      isImageGenerationEnabled: !s.isImageGenerationEnabled,
                    }))
                  }
                />
              </div>
              {settings.isImageGenerationEnabled && (
                <div className="border-t border-dashed border-gray-200 dark:border-zinc-600 mt-3 pt-4">
                  <div className="rounded-md border border-gray-200 bg-gray-50 p-4 dark:border-zinc-600 dark:bg-zinc-800/40">
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm font-medium">Provider</p>
                        <p className="text-xs text-muted-foreground">
                          Image generation API type: OpenAI-compatible or DashScope native API
                        </p>
                        <div className="mt-1.5 flex gap-2">
                          <button
                            type="button"
                            className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                              settings.imageGenerationProvider === "openai"
                                ? "border-violet-300 bg-violet-50 text-violet-700 dark:border-violet-600 dark:bg-violet-900/30 dark:text-violet-300"
                                : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
                            }`}
                            onClick={() =>
                              setSettings((s) => ({
                                ...s,
                                imageGenerationProvider: "openai",
                              }))
                            }
                          >
                            OpenAI
                          </button>
                          <button
                            type="button"
                            className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                              settings.imageGenerationProvider === "dashscope"
                                ? "border-violet-300 bg-violet-50 text-violet-700 dark:border-violet-600 dark:bg-violet-900/30 dark:text-violet-300"
                                : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
                            }`}
                            onClick={() =>
                              setSettings((s) => ({
                                ...s,
                                imageGenerationProvider: "dashscope",
                              }))
                            }
                          >
                            DashScope
                          </button>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium">Base URL</p>
                        <p className="text-xs text-muted-foreground">
                          {settings.imageGenerationProvider === "dashscope"
                            ? "DashScope native API endpoint, e.g. https://dashscope.aliyuncs.com or your TokenPlan tenant URL"
                            : "Optional, leave empty to use the default OpenAI API URL"}
                        </p>
                        <Input
                          className="mt-1.5"
                          placeholder={settings.imageGenerationProvider === "dashscope"
                            ? "https://dashscope.aliyuncs.com/compatible-mode/v1"
                            : "https://api.openai.com/v1"}
                          value={settings.imageGenerationBaseUrl || ""}
                          onChange={(e) =>
                            setSettings((s) => ({
                              ...s,
                              imageGenerationBaseUrl: e.target.value || null,
                            }))
                          }
                        />
                      </div>
                      <div>
                        <p className="text-sm font-medium">API Key</p>
                        <p className="text-xs text-muted-foreground">
                          Image generation API key, leave empty to use the code generation key
                        </p>
                        <Input
                          className="mt-1.5"
                          type="password"
                          placeholder="sk-..."
                          value={settings.imageGenerationApiKey || ""}
                          onChange={(e) =>
                            setSettings((s) => ({
                              ...s,
                              imageGenerationApiKey: e.target.value || null,
                            }))
                          }
                        />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Model</p>
                        <p className="text-xs text-muted-foreground">
                          {settings.imageGenerationProvider === "dashscope"
                            ? "DashScope image model, e.g. wan2.7-image-pro, qwen-image-2.0"
                            : "OpenAI-compatible image model, e.g. dall-e-3"}
                        </p>
                        <Input
                          className="mt-1.5"
                          placeholder={settings.imageGenerationProvider === "dashscope" ? "wan2.7-image-pro" : "dall-e-3"}
                          value={settings.imageGenerationModel || ""}
                          onChange={(e) =>
                            setSettings((s) => ({
                              ...s,
                              imageGenerationModel: e.target.value || null,
                            }))
                          }
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Screenshot by URL */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                Screenshot by URL
              </h2>
            </div>
            <div className="p-4">
              <p className="text-xs text-gray-500 dark:text-zinc-400">
                If you want to use URLs directly instead of taking the screenshot
                yourself, add a ScreenshotOne API key.{" "}
                <a
                  href="https://screenshotone.com?via=screenshot-to-code"
                  className="text-violet-600 hover:text-violet-700 dark:text-violet-400 dark:hover:text-violet-300"
                  target="_blank"
                >
                  Get 100 screenshots/mo for free.
                </a>
              </p>
              <Input
                id="screenshot-one-api-key"
                className="mt-3"
                placeholder="ScreenshotOne API key"
                value={settings.screenshotOneApiKey || ""}
                onChange={(e) =>
                  setSettings((s) => ({
                    ...s,
                    screenshotOneApiKey: e.target.value,
                  }))
                }
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsTab;
