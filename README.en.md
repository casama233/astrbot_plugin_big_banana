# 🍌 Big Banana — AstrBot Image and Video Generation

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · **English**

A multi-provider AstrBot plugin for image/video generation, reference images, prompt presets, LLM tools, background jobs and third-party callbacks.

**V2 (`v0.2.x`) has a new configuration structure and generation pipeline and is not guaranteed to be compatible with V1 settings or runtime data.** See [changelog.md](changelog.md). The source README lists **AstrBot 4.26.0+** and **Python 3.11+**.

## Features

- Image APIs: Gemini, OpenAI Chat/Images/Responses, MiniMax, SiliconFlow, Agnes and streaming-compatible endpoints.
- Optional Vertex AI Anonymous reverse provider. The source describes no per-user generation-count cap, but **availability is not guaranteed and depends on provider load, network and service behavior**; the original description mentions PNG up to 4K/18 MB.
- Asynchronous CogVideoX-Flash text-to-video and image-to-video tasks.
- LLM image/video tools, preset lookup and optional assistant-model prompt optimization.
- Configurable presets, placeholders, aliases, multiple keys, provider ordering and fallback.
- In-message, quoted, fixed-reference and avatar images; multi-message collection.
- Group cooldowns, user/group allowlists, command prefixes and mixed triggering.
- URL-only output, local save, R2 storage and optional privacy metadata stripping.

## Commands (original Chinese syntax)

| Command | Meaning |
| --- | --- |
| `<trigger>` | Generate images with the named preset |
| `bnv <prompt>` | CogVideoX-Flash video; attached image becomes the first frame |
| `/lm添加 <trigger> <prompt>` | Add a preset |
| `/lm删除 <trigger>` | Delete a preset |
| `/lm列表` | List presets |
| `/lm提示词 <trigger>` | Show a preset |
| `/lm白名单添加 <用户/群组> <ID/SID>` | Add allowlist entry |
| `/lm白名单删除 <用户/群组> <ID/SID>` | Remove allowlist entry |
| `/lm白名单列表` | Show allowlist |

**Documentation translations do not create English command aliases.**

## Prompt options

Arguments follow the trigger and are separated by spaces: `bnn prompt --image_size 4K --google_search`.

| Option | Behavior |
| --- | --- |
| `--min_images` / `--max_images` | Minimum/maximum non-negative reference-image count; provider limits apply |
| `--aspect_ratio` | Desired ratio, e.g. `1:1`, `16:9`, `21:9`; model may ignore it |
| `--image_size` | `1K`, `2K`, `4K` for supported Gemini models |
| `--google_search` | Boolean Google Search toggle for certain Gemini models |
| `--refer_images` | Comma-separated preset image filenames without spaces |
| `--gather_mode` | Collect multiple prompts/images before generation |
| `--providers` | Override provider order, e.g. comma-separated `Provider/Model` |
| `--n` / `--size` | OpenAI Images API count and dimensions only |
| `--url` | Return the actual image URL instead of media, when provider supports it |
| `--capability` | `image_generation` or `video_generation` |
| `--quality` / `--fps` | `speed/quality` and video 30/60 FPS |
| `--with_audio` / `--watermark_enabled` | AI audio and watermark toggles |

`--aspect_ratio` applies to Gemini-native requests; `--image_size` and `--google_search` are limited to some `gemini-3` models. Supported QQ, Telegram and Discord adapters may supplement missing reference images with mentioned users', sender or bot avatars, according to configuration. Store fixed reference images under `plugin_data/astrbot_plugin_big_banana/refer_images/`.

Collection mode is completed with the Chinese message **「开始」** and cancelled with **「取消」**. Disabled/incompatible providers are skipped. `--url` cannot work if the provider returns binary image data without an actual URL.

## Built-in presets

- `bnn`: image-to-image, requires at least one image.
- `bnt`: text-to-image, no minimum images.
- `bna`: collect prompts and images until 「开始」 or 「取消」.
- `bnv`: video generation, at most one reference image.
- `llm_default`: default LLM image tool preset, 0–6 images.
- `llm_video_default`: default LLM video tool preset, maximum one image.
- `手办化`: figurine-style image preset.

A configured preset with the same name overrides the built-in preset. An empty LLM tool preset name does **not** automatically enable these defaults.

## Background callback for tool-generated media

When background tool execution is enabled and a callback plugin and method are configured, Big Banana invokes the designated AstrBot plugin when a task finishes.

Callbacks receive **five keyword arguments**: `event: AstrMessageEvent`, `result: MessageChain`, `params: dict`, `unified_msg_origin: str`, `is_success: bool`. Use `is_success` to determine success instead of parsing message text.

```python
async def on_media_generation_complete(self, *, event, result, params, unified_msg_origin, is_success) -> bool:
    await self.handle_background_result(event=event, result=result, params=params,
                                        unified_msg_origin=unified_msg_origin, is_success=is_success)
    return True
```

Return `True` when the caller consumed the result; `False` requests Big Banana's fallback. Non-boolean returns (including `None`) are treated as consumed for legacy compatibility. Missing/raising callbacks trigger fallback. Async generators use their last yielded value. With **direct media sending disabled**, callbacks receive the unsent media; with it **enabled**, Big Banana sends media first and provides only a textual completion status. Treat `params` as read-only; callers own retry and idempotency.

For [Giftia](https://github.com/sukafon/astrbot_plugin_giftia), set the callback plugin to `astrbot_plugin_giftia` and method to `on_drawing_complete`.

## Troubleshooting, license and credits

Images over 10 MB on Telegram are sent as files, since large image messages may fail and older error paths can fill logs with Base64. LLM tool-loop issues were fixed in AstrBot 4.25+; update AstrBot if encountered.

Forked from [sukafon/astrbot_plugin_big_banana](https://github.com/sukafon/astrbot_plugin_big_banana), under [MIT](LICENSE). Preserve sukafon's upstream copyright notice. Thanks to contributors, testers and coding-assistance tools; this fork does not relicense third-party content.
