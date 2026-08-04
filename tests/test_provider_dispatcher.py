from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from core.config.provider_config import ProviderConfigManager
from core.drawing.dispatcher import ProviderDispatcher
from core.schemas import GenerationResult, ImageResource, ProviderConfig


def build_dispatcher(*, fallback_on_empty_result: bool) -> ProviderDispatcher:
    plugin = SimpleNamespace(
        common_config=SimpleNamespace(
            fallback_on_empty_result=fallback_on_empty_result
        ),
        provider_config_manager=SimpleNamespace(default_providers=["first", "second"]),
    )
    dispatcher = ProviderDispatcher(plugin)
    dispatcher._get_provider_config = AsyncMock(
        side_effect=[
            ProviderConfig(name="first", provider_type="test"),
            ProviderConfig(name="second", provider_type="test"),
        ]
    )
    return dispatcher


@pytest.mark.asyncio
async def test_empty_result_continues_to_next_provider_when_enabled() -> None:
    dispatcher = build_dispatcher(fallback_on_empty_result=True)
    image = ImageResource("image/png", b"image")
    dispatcher._dispatch_provider = AsyncMock(
        side_effect=[GenerationResult(), GenerationResult(images=[image])]
    )

    result = await dispatcher.dispatch({"prompt": "test"}, None)

    assert result.images == [image]
    assert dispatcher._dispatch_provider.await_count == 2


@pytest.mark.asyncio
async def test_empty_result_stops_fallback_when_disabled() -> None:
    dispatcher = build_dispatcher(fallback_on_empty_result=False)
    empty_result = GenerationResult()
    dispatcher._dispatch_provider = AsyncMock(
        side_effect=[empty_result, GenerationResult(error_message="should not run")]
    )

    result = await dispatcher.dispatch({"prompt": "test"}, None)

    assert result is empty_result
    dispatcher._dispatch_provider.assert_awaited_once()


@pytest.mark.asyncio
async def test_all_empty_results_return_a_clear_error_when_fallback_enabled() -> None:
    dispatcher = build_dispatcher(fallback_on_empty_result=True)
    dispatcher._dispatch_provider = AsyncMock(
        side_effect=[GenerationResult(), GenerationResult()]
    )

    result = await dispatcher.dispatch({"prompt": "test"}, None)

    assert result.error_message == "提供商 second 未返回图片"
    assert dispatcher._dispatch_provider.await_count == 2


@pytest.mark.asyncio
async def test_template_provider_model_override_is_request_scoped() -> None:
    provider_config_manager = ProviderConfigManager(
        {
            "provider_template": [
                {
                    "name": "gpt2",
                    "provider_type": "OpenAI_Images",
                    "capability": "image_generation",
                    "enabled": True,
                    "enabled_as_default": False,
                    "fallback_order": 0,
                    "model": "gpt-image-1",
                }
            ],
            "default_astr_providers": [],
        }
    )
    configured_provider = provider_config_manager.provider_configs["gpt2"]
    get_native_provider = AsyncMock(return_value=None)
    plugin = SimpleNamespace(
        provider_config_manager=provider_config_manager,
        context=SimpleNamespace(
            provider_manager=SimpleNamespace(
                get_provider_by_id=get_native_provider,
            )
        ),
    )
    dispatcher = ProviderDispatcher(plugin)
    overridden = await dispatcher._get_provider_config("gpt2/gpt-image-2")
    unchanged = await dispatcher._get_provider_config("gpt2")

    assert overridden is not configured_provider
    assert overridden is not None
    assert overridden.name == "gpt2"
    assert overridden.model == "gpt-image-2"
    assert unchanged is configured_provider
    assert configured_provider.model == "gpt-image-1"
    get_native_provider.assert_not_awaited()
