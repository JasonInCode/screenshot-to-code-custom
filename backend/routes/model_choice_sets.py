from llm import Llm, MODEL_PROVIDER

# Video variants always use Gemini.
VIDEO_VARIANT_MODELS = (
    Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
    Llm.GEMINI_3_1_PRO_PREVIEW_HIGH,
)

# All API keys available.

# Image (Create)

ALL_KEYS_MODELS_DEFAULT = (
    Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
    Llm.GPT_5_2_CODEX_HIGH,
    Llm.GEMINI_3_FLASH_PREVIEW_HIGH,
    Llm.GEMINI_3_1_PRO_PREVIEW_HIGH,
)

# Text (Create)

ALL_KEYS_MODELS_TEXT_CREATE = (
    Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
    Llm.GPT_5_2_CODEX_HIGH,
    Llm.CLAUDE_OPUS_4_6,
    Llm.GEMINI_3_1_PRO_PREVIEW_LOW,
)

# Image + Text (Update)

ALL_KEYS_MODELS_UPDATE = (
    Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
    Llm.GPT_5_4_2026_03_05_LOW,
)

# Key subset fallbacks.
GEMINI_ANTHROPIC_MODELS = (
    Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
    Llm.GEMINI_3_1_PRO_PREVIEW_LOW,
    Llm.CLAUDE_OPUS_4_6,
    Llm.GEMINI_3_FLASH_PREVIEW_HIGH,
    Llm.GEMINI_3_1_PRO_PREVIEW_HIGH,
)
GEMINI_OPENAI_MODELS = (
    Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
    Llm.GEMINI_3_1_PRO_PREVIEW_LOW,
    Llm.GPT_5_2_CODEX_HIGH,
    Llm.GPT_5_2_CODEX_MEDIUM,
)
OPENAI_ANTHROPIC_MODELS = (
    Llm.CLAUDE_OPUS_4_6,
    Llm.GPT_5_2_CODEX_HIGH,
    Llm.GPT_5_2_CODEX_MEDIUM,
)
GEMINI_ONLY_MODELS = (
    Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
    Llm.GEMINI_3_1_PRO_PREVIEW_LOW,
    Llm.GEMINI_3_FLASH_PREVIEW_HIGH,
    Llm.GEMINI_3_1_PRO_PREVIEW_HIGH,
)
ANTHROPIC_ONLY_MODELS = (
    Llm.CLAUDE_OPUS_4_6,
    Llm.CLAUDE_SONNET_4_6,
)
OPENAI_ONLY_MODELS = (
    Llm.GPT_5_2_CODEX_HIGH,
    Llm.GPT_5_2_CODEX_MEDIUM,
)


def get_model_choice_set_for_custom_model(
    model_value: str,
    selected_provider: str | None = None,
) -> tuple[Llm, ...]:
    """自定义模型根据 provider 归属走单 provider 选择集"""
    # 尝试匹配已知 Llm enum 值
    for llm_model in Llm:
        if llm_model.value == model_value:
            provider = MODEL_PROVIDER.get(llm_model)
            if provider == "openai":
                return OPENAI_ONLY_MODELS
            if provider == "anthropic":
                return ANTHROPIC_ONLY_MODELS
            if provider == "gemini":
                return GEMINI_ONLY_MODELS
            return ALL_KEYS_MODELS_DEFAULT

    # 完全自定义模型 ID：优先使用前端传入的 provider 归属
    if selected_provider == "openai":
        return OPENAI_ONLY_MODELS
    if selected_provider == "anthropic":
        return ANTHROPIC_ONLY_MODELS
    if selected_provider == "gemini":
        return GEMINI_ONLY_MODELS

    # 无 provider 信息，默认走全量选择集
    return ALL_KEYS_MODELS_DEFAULT
