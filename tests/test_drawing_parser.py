from types import SimpleNamespace

from core.config.prompt_config import PromptConfigManager
from core.drawing.parser import parse_params

import astrbot.api.message_components as Comp


class FakeEvent:
    is_at_or_wake_command = False

    def __init__(
        self,
        text: str,
        *,
        platform_name: str = "test",
        mentions: list[SimpleNamespace] | None = None,
        extra_messages: list[object] | None = None,
    ) -> None:
        self.platform_meta = SimpleNamespace(name=platform_name)
        self.message_obj = SimpleNamespace(
            raw_message=SimpleNamespace(mentions=mentions or [])
        )
        self._messages = [Comp.Plain(text), *(extra_messages or [])]

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


def test_gather_preset_keeps_empty_prompt_until_generation() -> None:
    plugin = build_plugin(
        ["bna {{user_text}} --min_images 0 --gather_mode"],
        [],
    )

    params = parse_params(plugin, FakeEvent("bna"))

    assert params == {
        "prompt": "",
        "min_images": 0,
        "gather_mode": True,
    }


def test_prompt_uses_at_nickname_without_id() -> None:
    plugin = build_plugin([], ["provider"])
    event = FakeEvent(
        "provider two people",
        extra_messages=[Comp.At(qq="123", name="Alice")],
    )

    params = parse_params(plugin, event)

    assert params == {"prompt": "two people @Alice", "providers": ["provider"]}


def test_qq_official_text_mentions_are_cleaned_to_nicknames() -> None:
    plugin = build_plugin([], ["provider"])
    event = FakeEvent(
        "provider <@AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA>和"
        "<@BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB>合影",
        platform_name="qq_official",
        mentions=[
            SimpleNamespace(
                id="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", username="Alice"
            ),
            SimpleNamespace(
                id="BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB", username="Bob"
            ),
        ],
    )

    params = parse_params(plugin, event)

    assert params == {
        "prompt": "@Alice和@Bob合影",
        "providers": ["provider"],
    }


def test_prompt_mention_without_nickname_falls_back_to_id() -> None:
    plugin = build_plugin([], ["provider"])
    event = FakeEvent(
        "provider <@AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA>合影",
        platform_name="qq_official",
    )

    params = parse_params(plugin, event)

    assert params == {
        "prompt": "@AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA合影",
        "providers": ["provider"],
    }
