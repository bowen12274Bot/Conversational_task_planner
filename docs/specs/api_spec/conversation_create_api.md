# 建立對話 API 規格

## 文件名稱

- `conversation_create_api`

## API 端點

- `POST /api/conversations`

## API 目的

- 提供前端於初始化時建立新的 `conversation`
- 讓後端控制層呼叫 `Persistence Layer` 生成新的 `conversation_id`
- 回傳可供後續 `raw_request` 與歷史紀錄查詢使用的對話識別值

## 輸入內容

- 本 API 現階段不要求前端提供額外輸入內容

## 成功條件

- 後端成功建立新的 `conversation`
- `Persistence Layer` 成功生成並保存新的 `conversation_id`

## 回應訊息

- 成功時，回傳新建立的 `conversation_id`
- 失敗時，回傳錯誤狀態與最小錯誤資訊

## 最小回應資料

- `conversation_id`

其中：

- `conversation_id`
  - 指本次新建立對話的識別值，供前端後續互動與歷史查詢使用。

## 狀態碼

| 狀態碼 | 名稱 | 說明 |
|---|---|---|
| `200` | `OK` | 成功建立新的 `conversation`，並回傳可用的 `conversation_id` |
| `500` | `Internal Server Error` | 後端在建立 `conversation` 或保存資料時發生錯誤 |

## 錯誤訊息格式

在 `500 Internal Server Error` 情境下，回應中至少應包含：

- `error_message`
- `error_stage`

## 名詞定義

- `error_message`
  - 本次錯誤的簡短描述。

- `error_stage`
  - 錯誤發生的處理位置，例如控制層、`Persistence Layer` 或資料保存階段。
