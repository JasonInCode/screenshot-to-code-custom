import * as React from "react";
import {
  CODE_GENERATION_MODEL_DESCRIPTIONS,
  getModelDisplayName,
} from "@/lib/models";
import { cn } from "@/lib/utils";

interface Props {
  value: string;
  onChange: (value: string) => void;
  presetModels: string[];
  placeholder?: string;
}

const ModelCombobox = React.forwardRef<HTMLInputElement, Props>(
  ({ value, onChange, presetModels, placeholder = "Select or type a model ID" }, ref) => {
    // 下拉框开关状态
    const [isOpen, setIsOpen] = React.useState(false);
    // 过滤查询状态（仅用于过滤下拉列表，不控制输入框值）
    const [query, setQuery] = React.useState(value);
    // 容器引用，用于检测外部点击
    const containerRef = React.useRef<HTMLDivElement>(null);

    // 当外部 value 变化时同步过滤查询
    React.useEffect(() => {
      setQuery(value);
    }, [value]);

    // 点击外部关闭下拉框
    React.useEffect(() => {
      function handleClickOutside(event: MouseEvent) {
        if (
          containerRef.current &&
          !containerRef.current.contains(event.target as Node)
        ) {
          setIsOpen(false);
        }
      }
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // 根据过滤查询过滤预设模型
    const filteredPresets = presetModels.filter((model) => {
      const displayName = getModelDisplayName(model);
      const lowerQuery = query.toLowerCase();
      return (
        model.toLowerCase().includes(lowerQuery) ||
        displayName.toLowerCase().includes(lowerQuery)
      );
    });

    // 处理输入变化：更新过滤查询并通知外部
    function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
      const newValue = e.target.value;
      setQuery(newValue);
      onChange(newValue);
      setIsOpen(true);
    }

    // 处理预设模型选择
    function handlePresetSelect(model: string) {
      setQuery(model);
      onChange(model);
      setIsOpen(false);
    }

    // 处理输入框聚焦
    function handleInputFocus() {
      setIsOpen(true);
    }

    // 键盘处理：Escape 关闭下拉框
    function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    }

    return (
      <div
        ref={containerRef}
        className="relative"
        role="combobox"
        aria-expanded={isOpen}
      >
        <input
          ref={ref}
          type="text"
          value={value}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          aria-autocomplete="list"
          aria-controls="model-combobox-listbox"
          className={cn(
            "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors",
            "placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
            "disabled:cursor-not-allowed disabled:opacity-50"
          )}
        />

        {isOpen && (
          <div
            id="model-combobox-listbox"
            role="listbox"
            className={cn(
              "absolute z-50 mt-1 w-full rounded-md border shadow-md",
              "border bg-popover text-popover-foreground",
              "max-h-[240px] overflow-y-auto"
            )}
          >
            {/* 预设模型列表 */}
            {filteredPresets.length > 0 ? (
              <div className="p-1">
                {filteredPresets.map((model) => {
                  const desc = CODE_GENERATION_MODEL_DESCRIPTIONS[model];
                  const displayName = getModelDisplayName(model);
                  const isSelected = value === model;
                  return (
                    <button
                      key={model}
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => handlePresetSelect(model)}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm outline-none",
                        "transition-colors hover:bg-accent hover:text-accent-foreground",
                        isSelected && "bg-accent text-accent-foreground"
                      )}
                    >
                      <span className="flex-1 truncate">{displayName}</span>
                      {desc?.inBeta && (
                        <span
                          className={cn(
                            "inline-flex items-center rounded px-1.5 py-0.5 text-xs font-semibold",
                            "bg-orange-100 text-orange-700",
                            "dark:bg-orange-900/30 dark:text-orange-300"
                          )}
                        >
                          Beta
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="px-3 py-2 text-sm text-muted-foreground">
                No matching preset models
              </div>
            )}

            {/* 底部提示 */}
            <div
              className={cn(
                "border-t px-3 py-2 text-xs",
                "border-border text-muted-foreground"
              )}
            >
              Or type a custom model ID above
            </div>
          </div>
        )}
      </div>
    );
  }
);

ModelCombobox.displayName = "ModelCombobox";

export { ModelCombobox };