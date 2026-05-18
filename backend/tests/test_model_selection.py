import pytest
from unittest.mock import AsyncMock
from routes.generate_code import ModelSelectionStage
from routes.model_choice_sets import (
    ANTHROPIC_ONLY_MODELS,
    GEMINI_ONLY_MODELS,
    OPENAI_ONLY_MODELS,
    ALL_KEYS_MODELS_DEFAULT,
    ALL_KEYS_MODELS_TEXT_CREATE,
    get_model_choice_set_for_custom_model,
)
from llm import Llm


class TestModelSelectionAllKeys:
    """Test model selection when Gemini, Anthropic, and OpenAI API keys are present."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_throw_error = AsyncMock()
        self.model_selector = ModelSelectionStage(mock_throw_error)

    @pytest.mark.asyncio
    async def test_gemini_anthropic_create(self):
        """All keys: fixed order for four variants."""
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="text",
            openai_api_key="key",
            anthropic_api_key="key",
            gemini_api_key="key",
        )

        expected = [
            Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
            Llm.GPT_5_2_CODEX_HIGH,
            Llm.CLAUDE_OPUS_4_6,
            Llm.GEMINI_3_1_PRO_PREVIEW_LOW,
        ]
        assert models == expected

    @pytest.mark.asyncio
    async def test_gemini_anthropic_update_text(self):
        """All keys text update: uses two fast edit variants."""
        models = await self.model_selector.select_models(
            generation_type="update",
            input_mode="text",
            openai_api_key="key",
            anthropic_api_key="key",
            gemini_api_key="key",
        )

        expected = [
            Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
            Llm.GPT_5_4_2026_03_05_LOW,
        ]
        assert models == expected

    @pytest.mark.asyncio
    async def test_gemini_anthropic_update(self):
        """All keys image update: uses two fast edit variants."""
        models = await self.model_selector.select_models(
            generation_type="update",
            input_mode="image",
            openai_api_key="key",
            anthropic_api_key="key",
            gemini_api_key="key",
        )

        expected = [
            Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
            Llm.GPT_5_4_2026_03_05_LOW,
        ]
        assert models == expected

    @pytest.mark.asyncio
    async def test_video_create_prefers_gemini_minimal_then_3_1_high(self):
        """Video create always uses two Gemini variants in fixed order."""
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="video",
            openai_api_key="key",
            anthropic_api_key="key",
            gemini_api_key="key",
        )

        expected = [
            Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
            Llm.GEMINI_3_1_PRO_PREVIEW_HIGH,
        ]
        assert models == expected

    @pytest.mark.asyncio
    async def test_video_update_prefers_gemini_minimal_then_3_1_high(self):
        """Video update always uses the same two Gemini variants as video create."""
        models = await self.model_selector.select_models(
            generation_type="update",
            input_mode="video",
            openai_api_key="key",
            anthropic_api_key="key",
            gemini_api_key="key",
        )

        expected = [
            Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL,
            Llm.GEMINI_3_1_PRO_PREVIEW_HIGH,
        ]
        assert models == expected


class TestModelSelectionOpenAIAnthropic:
    """Test model selection when only OpenAI and Anthropic keys are present."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_throw_error = AsyncMock()
        self.model_selector = ModelSelectionStage(mock_throw_error)

    @pytest.mark.asyncio
    async def test_openai_anthropic(self):
        """OpenAI + Anthropic: Claude Opus 4.6, GPT 5.2 Codex (high/medium), cycling"""
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="text",
            openai_api_key="key",
            anthropic_api_key="key",
            gemini_api_key=None,
        )

        expected = [
            Llm.CLAUDE_OPUS_4_6,
            Llm.GPT_5_2_CODEX_HIGH,
            Llm.GPT_5_2_CODEX_MEDIUM,
            Llm.CLAUDE_OPUS_4_6,
        ]
        assert models == expected


class TestModelSelectionAnthropicOnly:
    """Test model selection when only Anthropic key is present."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_throw_error = AsyncMock()
        self.model_selector = ModelSelectionStage(mock_throw_error)

    @pytest.mark.asyncio
    async def test_anthropic_only(self):
        """Anthropic only: Claude Opus 4.6 and Claude Sonnet 4.6 cycling"""
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="text",
            openai_api_key=None,
            anthropic_api_key="key",
            gemini_api_key=None,
        )

        expected = [
            Llm.CLAUDE_OPUS_4_6,
            Llm.CLAUDE_SONNET_4_6,
            Llm.CLAUDE_OPUS_4_6,
            Llm.CLAUDE_SONNET_4_6,
        ]
        assert models == expected


class TestModelSelectionOpenAIOnly:
    """Test model selection when only OpenAI key is present."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_throw_error = AsyncMock()
        self.model_selector = ModelSelectionStage(mock_throw_error)

    @pytest.mark.asyncio
    async def test_openai_only(self):
        """OpenAI only: GPT 5.2 Codex (high/medium) only"""
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="text",
            openai_api_key="key",
            anthropic_api_key=None,
            gemini_api_key=None,
        )

        expected = [
            Llm.GPT_5_2_CODEX_HIGH,
            Llm.GPT_5_2_CODEX_MEDIUM,
            Llm.GPT_5_2_CODEX_HIGH,
            Llm.GPT_5_2_CODEX_MEDIUM,
        ]
        assert models == expected


class TestModelSelectionNoKeys:
    """Test model selection when no API keys are present."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_throw_error = AsyncMock()
        self.model_selector = ModelSelectionStage(mock_throw_error)

    @pytest.mark.asyncio
    async def test_no_keys_raises_error(self):
        """No keys: Should raise an exception"""
        with pytest.raises(Exception, match="No API key"):
            await self.model_selector.select_models(
                generation_type="create",
                input_mode="text",
                openai_api_key=None,
                anthropic_api_key=None,
                gemini_api_key=None,
            )


class TestGetModelChoiceSetForCustomModel:
    """根据自定义模型值返回对应 provider 选择集"""

    def test_known_openai_model_returns_openai_only(self):
        """已知 OpenAI 模型返回 OPENAI_ONLY_MODELS"""
        result = get_model_choice_set_for_custom_model("gpt-5.2-codex (high thinking)")
        assert result == OPENAI_ONLY_MODELS

    def test_known_anthropic_model_returns_anthropic_only(self):
        """已知 Anthropic 模型返回 ANTHROPIC_ONLY_MODELS"""
        result = get_model_choice_set_for_custom_model("claude-opus-4-6")
        assert result == ANTHROPIC_ONLY_MODELS

    def test_known_gemini_model_returns_gemini_only(self):
        """已知 Gemini 模型返回 GEMINI_ONLY_MODELS"""
        result = get_model_choice_set_for_custom_model("gemini-3-flash-preview (minimal thinking)")
        assert result == GEMINI_ONLY_MODELS

    def test_unknown_model_without_provider_defaults_to_all_keys(self):
        """完全自定义模型 ID 无 provider 信息时返回 ALL_KEYS_MODELS_DEFAULT"""
        result = get_model_choice_set_for_custom_model("my-custom-model-id")
        assert result == ALL_KEYS_MODELS_DEFAULT

    def test_unknown_model_with_openai_provider_returns_openai_only(self):
        """完全自定义模型 ID 指定 openai provider 时返回 OPENAI_ONLY_MODELS"""
        result = get_model_choice_set_for_custom_model(
            "my-custom-gpt", selected_provider="openai"
        )
        assert result == OPENAI_ONLY_MODELS

    def test_unknown_model_with_anthropic_provider_returns_anthropic_only(self):
        """完全自定义模型 ID 指定 anthropic provider 时返回 ANTHROPIC_ONLY_MODELS"""
        result = get_model_choice_set_for_custom_model(
            "my-custom-claude", selected_provider="anthropic"
        )
        assert result == ANTHROPIC_ONLY_MODELS

    def test_unknown_model_with_gemini_provider_returns_gemini_only(self):
        """完全自定义模型 ID 指定 gemini provider 时返回 GEMINI_ONLY_MODELS"""
        result = get_model_choice_set_for_custom_model(
            "my-custom-gemini", selected_provider="gemini"
        )
        assert result == GEMINI_ONLY_MODELS

    def test_known_model_ignores_selected_provider(self):
        """已知模型始终按其自身 provider 归属路由，忽略 selected_provider"""
        # claude-opus-4-6 是 Anthropic 模型，即使传入 selected_provider="openai"
        # 也应返回 ANTHROPIC_ONLY_MODELS
        result = get_model_choice_set_for_custom_model(
            "claude-opus-4-6", selected_provider="openai"
        )
        assert result == ANTHROPIC_ONLY_MODELS


class TestModelSelectionWithCustomModel:
    """测试带 code_generation_model 参数的模型选择"""

    def setup_method(self):
        mock_throw_error = AsyncMock()
        self.model_selector = ModelSelectionStage(mock_throw_error)

    @pytest.mark.asyncio
    async def test_custom_model_returns_same_string_for_all_variants(self):
        """自定义模型（不在 Llm enum 中）所有 variant 直接使用该模型字符串"""
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="text",
            openai_api_key="key",
            anthropic_api_key="key",
            gemini_api_key="key",
            code_generation_model="qwen3.6-plus",
            selected_api_provider="openai",
        )
        # 自定义模型字符串直接用于所有 variant，不循环预设值
        expected = ["qwen3.6-plus", "qwen3.6-plus", "qwen3.6-plus", "qwen3.6-plus"]
        assert models == expected

    @pytest.mark.asyncio
    async def test_custom_model_without_provider_returns_string_for_all_variants(self):
        """自定义模型无 provider 信息时也直接返回模型字符串"""
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="text",
            openai_api_key="key",
            anthropic_api_key="key",
            gemini_api_key="key",
            code_generation_model="my-custom-gpt",
        )
        expected = ["my-custom-gpt", "my-custom-gpt", "my-custom-gpt", "my-custom-gpt"]
        assert models == expected

    @pytest.mark.asyncio
    async def test_known_model_uses_existing_key_based_logic(self):
        """已知模型（在 Llm enum 中）走现有 API key 逻辑"""
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="text",
            openai_api_key="key",
            anthropic_api_key="key",
            gemini_api_key="key",
            code_generation_model="claude-opus-4-6",
        )
        # 已知模型在 enum 中，走正常的 API key 逻辑
        expected = list(ALL_KEYS_MODELS_TEXT_CREATE)
        assert models == expected