# 🍌 Big Banana — AstrBot 圖片／影片生成插件

[简体中文](README.md) · **繁體中文** · [English](README.en.md)

AstrBot 多提供者的圖片與影片生成插件，支援多圖參考、提示詞預設、LLM 工具、背景工作及第三方回呼。

**V2（`v0.2.x`）使用新的設定結構與生成流程，不保證與 V1 設定或執行資料相容。** 更新資訊見 [changelog.md](changelog.md)。原 README 標示 AstrBot **4.26.0+**、Python **3.11+**。

## 功能

- 支援 Gemini、OpenAI Chat／Images／Responses、MiniMax、SiliconFlow、Agnes 等圖片介面，以及串流回應。
- 整合 Vertex AI Anonymous 逆向提供者；原項目稱其圖片生成次數不設限制，但**實際可用性取決於伺服器負載、網路與服務狀態，並非可用性保證**。原說明提及最高 4K／18 MB PNG。
- 智譜 `CogVideoX-Flash` 非同步文字生成影片、圖片生成影片。
- LLM 圖片／影片生成工具、預設查詢、副腦提示詞最佳化。
- 自訂預設、佔位符、參數別名、Provider 順序、多金鑰與失敗降級。
- 訊息內圖片、引用圖片、固定參考圖、QQ 頭像及多訊息收集。
- 群組冷卻、白名單、命令前綴與混合觸發模式。
- 可只傳回圖片 URL，或儲存在本機及 R2；上傳前可清除參考圖中繼資料。

## 命令（保留實際中文指令）

| 指令 | 功能 |
| --- | --- |
| `<觸發詞>` | 以相應預設生成圖片 |
| `bnv <提示詞>` | CogVideoX-Flash 影片；帶圖時作為首幀 |
| `/lm添加 <觸發詞> <提示詞內容>` | 新增預設 |
| `/lm删除 <觸發詞>` | 刪除預設 |
| `/lm列表` | 列出預設 |
| `/lm提示词 <觸發詞>` | 查看內容 |
| `/lm白名单添加 <用户/群组> <ID/SID>` | 新增白名單 |
| `/lm白名单删除 <用户/群组> <ID/SID>` | 移除白名單 |
| `/lm白名单列表` | 列出白名單 |

翻譯 README **不會改變實際的中文指令名稱**。

## 提示詞參數

觸發詞後可依空格傳入參數，例如 `bnn 提示詞 --image_size 4K --google_search`。

| 參數 | 作用 |
| --- | --- |
| `--min_images`／`--max_images` | 最少／最多參考圖數量（不可為負；上限受提供者限制） |
| `--aspect_ratio` | 畫面比例，例如 `1:1`、`16:9`、`21:9`；實際須模型支援 |
| `--image_size` | `1K`、`2K`、`4K`，適用特定 Gemini 模型 |
| `--google_search` | `true/false`，特定 Gemini 模型可用 |
| `--refer_images` | 固定參考圖片檔名，以英文逗號分隔，不含空白 |
| `--gather_mode` | 多訊息提示詞及圖片收集 |
| `--providers` | 自訂 Provider 次序，支援 `Provider/Model` 和逗號列表 |
| `--n`／`--size` | OpenAI Images API 專用生成數量／尺寸 |
| `--url` | 只返回提供者實際交付的圖片 URL |
| `--capability` | `image_generation` 或 `video_generation` |
| `--quality`／`--fps` | `speed/quality`、影片 30／60 FPS |
| `--with_audio`／`--watermark_enabled` | 影片音效及 AI 浮水印 |

`--aspect_ratio` 只對 Gemini 規格生效；`--image_size`／`--google_search` 限部分 `gemini-3` 模型。缺少參考圖片時，支援的 QQ、Telegram、Discord 等平台可依設定補入 @對象、發話者或機器人頭像；不足仍會報錯。固定參考圖放在 `plugin_data/astrbot_plugin_big_banana/refer_images/`。

收集模式以「开始」產生，以「取消」放棄；這是**實際指令文字**。Provider 名稱可用英文逗號指定多個，禁用或能力不符的 Provider 會被略過。若服務商只回傳圖片資料、沒有 URL，`--url` 不能生效。

## 預設

- `bnn`：圖生圖，最少一張參考圖片。
- `bnt`：純文字生成圖片。
- `bna`：收集多則文字及圖片，直到輸入「开始」或「取消」。
- `bnv`：影片生成，最多一張圖片；無圖時文字轉影片。
- `llm_default`：LLM 圖片工具預設，允許 0–6 張圖片。
- `llm_video_default`：LLM 影片工具預設，最多一張圖片。
- `手办化`：模型手辦化預設。

設定內的同名預設會覆蓋內建值；未指定 LLM 工具預設名稱不會自動套用這兩個內建預設。

## 背景生成回呼

啟用「工具呼叫使用背景任務」並填寫回呼插件與方法後，Big Banana 會在完成圖片／影片任務時通知指定的 AstrBot 插件。

回呼使用五個**關鍵字參數**：`event: AstrMessageEvent`、`result: MessageChain`、`params: dict`、`unified_msg_origin: str`、`is_success: bool`。以 `is_success` 判定成功，不要解析提示文字。

```python
async def on_media_generation_complete(self, *, event, result, params, unified_msg_origin, is_success) -> bool:
    await self.handle_background_result(event=event, result=result, params=params,
                                        unified_msg_origin=unified_msg_origin, is_success=is_success)
    return True
```

`True` 代表上游接管，`False` 代表 Big Banana 需要回退處理；`None` 等非布林回傳視作已接管。方法不存在或執行失敗會觸發回退。非同步生成器採最後一個 `yield`。**直接發送圖片結果關閉**時，回呼收到未發送的媒體；**開啟**時先發送媒體，回呼只收到文字完成狀態。應保持 `params` 唯讀，並由上游負責重試與冪等。

搭配 [Giftia](https://github.com/sukafon/astrbot_plugin_giftia) 時：背景回呼插件 `astrbot_plugin_giftia`、方法 `on_drawing_complete`。

## 排障、上游與授權

Telegram 超過 10 MB 的圖片會以檔案形式發送；舊版失敗路徑可能在日誌中輸出大量 Base64。模型工具循環呼叫問題已於 AstrBot 4.25+ 修復，遇到問題請更新 AstrBot。

本倉庫由 [sukafon/astrbot_plugin_big_banana](https://github.com/sukafon/astrbot_plugin_big_banana) fork，採 [MIT](LICENSE)，須保留原作者 sukafon 的版權聲明。感謝測試與開發貢獻者及程式輔助工具；分支修改不改變第三方資產的授權。
