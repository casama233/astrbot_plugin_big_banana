from types import SimpleNamespace

from core.config.prompt_config import PromptConfigManager
from core.drawing.parser import parse_params

import astrbot.api.message_components as Comp


class FakeEvent:
    is_at_or_wake_command = False

    def __init__(self, text: str) -> None:
        self._messages = [Comp.Plain(text)]

    def get_messages(self):
        return self._messages


def build_plugin(prompt_items: list[str], provider_names: list[str]):
    return SimpleNamespace(
        prefix_config=SimpleNamespace(
            prefix_list=[],
            coexist_enabled=False,
            provider_prefix=True,
        ),
        prompt_config_manager=PromptConfigManager({"prompt": prompt_items}),
        provider_config_manager=SimpleNamespace(
            provider_configs={
                name: SimpleNamespace(name=name) for name in provider_names
            }
        ),
        conf={"default_astr_providers": []},
        common_config=SimpleNamespace(preset_append=True),
    )


def test_preset_takes_priority_over_same_named_provider() -> None:
    plugin = build_plugin(
        ["same Poster {{user_text}} --max_images 2"],
        ["same"],
    )

    params = parse_params(plugin, FakeEvent("same cat"))

    assert params == {"prompt": "Poster cat", "max_images": 2}


def test_provider_prefix_uses_default_params_without_a_preset() -> None:
    plugin = build_plugin(
        ["style Styled {{user_text}} --max_images 2"],
        ["provider"],
    )

    params = parse_params(plugin, FakeEvent("provider cat --max_images 3"))

    assert params == {
        "prompt": "cat",
        "max_images": 3,
        "providers": ["provider"],
    }


def test_provider_prefix_can_still_select_a_preset() -> None:
    plugin = build_plugin(
        ["style Styled {{user_text}} --max_images 2"],
        ["provider"],
    )

    params = parse_params(plugin, FakeEvent("provider style cat"))

    assert params == {
        "prompt": "Styled cat",
        "max_images": 2,
        "providers": ["provider"],
    }
