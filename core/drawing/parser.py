from __future__ import annotations

from typing import TYPE_CHECKING, Any

import astrbot.api.message_components as Comp

if TYPE_CHECKING:
    from astrbot.api.event import AstrMessageEvent

    from ...main import BigBanana


def parse_params(plugin: BigBanana, event: AstrMessageEvent) -> dict[str, Any] | None:
    """解析消息事件中的绘图参数。未命中指令时快速返回 None。这里不负责收集图片，也不能修改消息链。"""

    # 提取首个有内容的 Plain 文本（目的是跳过开头是@的情况）
    first_text = ""
    first_component_idx = -1
    for idx, component in enumerate(event.get_messages()):
        if isinstance(component, Comp.Plain) and component.text.strip():
            first_text = component.text.strip()
            first_component_idx = idx
            break

    # 无有效文本，则不可能触发命令，直接返回 None
    if not first_text or first_component_idx == -1:
        return None

    # 命令前缀匹配
    matched_prefix = False
    for prefix in plugin.prefix_config.prefix_list:
        if first_text.startswith(prefix):
            # 去掉前缀，并去除前缀后的空格
            first_text = first_text.removeprefix(prefix).lstrip()
            matched_prefix = True
            break

    # 未 @ 机器人、未开启混合模式、配置了前缀但未匹配到前缀
    if (
        not event.is_at_or_wake_command
        and not plugin.prefix_config.coexist_enabled
        and plugin.prefix_config.prefix_list
        and not matched_prefix
    ):
        return None

    prompt_config = plugin.prompt_config_manager.prompt_config

    # 提供商前缀匹配。首词如果已经是预设名称，必须优先按预设处理，
    # 否则同名的提供商会先被剥离，导致后续无法找到预设。
    provider_names: list[str] = []
    if plugin.prefix_config.provider_prefix:
        token, _, rest = first_text.partition(" ")
        # 如果首词不是预设，才尝试将其解析为提供商前缀。
        if token and rest and token not in prompt_config:
            # token按逗号分割
            tokens = token.split(",")
            for t in tokens:
                provider_name = t.strip()
                template_config = plugin.provider_config_manager.provider_configs.get(
                    provider_name
                )
                if template_config:
                    provider_name = template_config.name
                elif provider_name not in plugin.conf.get("default_astr_providers", []):
                    provider_name = None
                # 匹配成功，去除提供商前缀和后续空格
                if provider_name:
                    provider_names.append(provider_name)
            if provider_names:
                first_text = rest.lstrip()

    # 提取预设指令和该组件内剩余文本
    cmd, _, cmd_rest = first_text.partition(" ")
    cmd = cmd.strip()

    # 未匹配提供商前缀时，必须命中预设；匹配到提供商前缀但没有预设时，
    # 将提供商前缀后的全部内容作为普通提示词，使用默认配置参数生成。
    if not cmd or cmd not in prompt_config:
        if not provider_names:
            return None

        params = plugin.prompt_config_manager.parse_prompt_params(
            _collect_user_text(event, first_component_idx, first_text)
        )
        params["providers"] = provider_names
        return params

    # 复制预设参数，防止污染全局预设。
    # 上游约束了非引用类型，这里只需浅拷贝即可。
    params = prompt_config[cmd].copy()
    # 如果有手动指定提供商，将覆盖预设中的提供商
    if provider_names:
        params["providers"] = provider_names

    preset_prompt = params.get("prompt", "")
    should_append_user_text = params.get(
        "preset_append", plugin.common_config.preset_append
    )
    # 有占位符时替换指定位置；启用补充时把用户文本追加到固定预设后。
    if "{{user_text}}" in preset_prompt or should_append_user_text:
        user_text = _collect_user_text(event, first_component_idx, cmd_rest)
        # 解析用户输入文本中的参数
        user_params = plugin.prompt_config_manager.parse_prompt_params(user_text)
        # 取出并删除用户提示词
        user_prompt = user_params.pop("prompt", "")
        if "{{user_text}}" in preset_prompt:
            params["prompt"] = preset_prompt.replace("{{user_text}}", user_prompt)
        elif user_prompt:
            params["prompt"] = f"{preset_prompt.rstrip()} {user_prompt}".strip()
        # 更新参数
        params.update(user_params)

    return params


def _collect_user_text(
    event: AstrMessageEvent,
    first_component_idx: int,
    first_component_text: str,
) -> str:
    """收集首个文本组件中已去除命令部分的用户文本及其余消息内容。"""

    message_parts = []
    for idx, comp in enumerate(event.get_messages()):
        if idx == first_component_idx:
            if first_component_text:
                message_parts.append(first_component_text)
        elif isinstance(comp, Comp.Plain) and comp.text:
            message_parts.append(comp.text)
        elif isinstance(comp, Comp.At) and comp.qq:
            message_parts.append(f"@{comp.name}({comp.qq})")
    return " ".join(message_parts).strip()
