import { ApiProvider } from "../../types";
import { API_PROVIDER_LABELS } from "../../lib/models";
import { Tabs, TabsList, TabsTrigger } from "../ui/tabs";

// 提供商选项列表
const PROVIDER_KEYS: ApiProvider[] = ["openai", "anthropic", "gemini"];

export interface ApiProviderSelectorProps {
  value: ApiProvider;
  onChange: (provider: ApiProvider) => void;
}

export function ApiProviderSelector({ value, onChange }: ApiProviderSelectorProps) {
  return (
    <Tabs
      value={value}
      onValueChange={(v) => onChange(v as ApiProvider)}
      className="w-full"
    >
      <TabsList className="grid w-full grid-cols-3">
        {PROVIDER_KEYS.map((provider) => (
          <TabsTrigger
            key={provider}
            value={provider}
            className="data-[state=active]:bg-violet-50 data-[state=active]:text-violet-700 dark:data-[state=active]:bg-violet-900/20 dark:data-[state=active]:text-violet-300"
          >
            {API_PROVIDER_LABELS[provider]}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}