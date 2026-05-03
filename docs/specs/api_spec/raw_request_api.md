# 原始需求 API 規格

## 文件名稱

- `raw_request_api`

## API 端點

- `POST /api/raw-request`

## API 目的

- 接收前端送出的原始需求輸入
- 啟動後端主流程
- 將本輪互動結果保存至持久化層
- 於主流程與輸出處理成功完成後，回傳成功結果

## 輸入內容

- 使用者原始句子
- `conversation_id`

其中：

- `conversation_id`
  - 表示本次請求所屬的既有對話識別值，供後端承接本輪互動與保存對話紀錄。

## 成功條件

- 主流程成功完成處理
- 輸出模組成功完成輸出
- 本輪互動資料成功寫入持久化層
- 請求已正確承接至指定的 `conversation`

## 回應訊息

- 成功時，回傳成功狀態、對應的 `conversation_id` 與輸出模組的最終輸出結果
- 失敗時，回傳錯誤狀態與最小錯誤資訊

## 最小成功回應資料

- `reply_text`
- `conversation_id`
- `structured_task_output`

其中：

- `reply_text`
  - 指本輪互動完成後，提供前端直接顯示的回覆文字。

- `conversation_id`
  - 指本輪互動所屬的既有對話識別值。

- `structured_task_output`
  - 指本輪互動若已有可供前端顯示的結構化任務資料，則由控制層一併回傳；若目前無可回傳資料，可為空值。

## 狀態碼

| 狀態碼 | 名稱 | 說明 |
|---|---|---|
| `200` | `OK` | 本次原始需求請求成功完成，且主流程與輸出模組皆已成功完成 |
| `400` | `Bad Request` | 請求內容不符合基本要求，例如缺少必要輸入內容、缺少 `conversation_id` 或輸入格式不正確 |
| `404` | `Not Found` | 已提供 `conversation_id`，但查無對應對話資料 |
| `500` | `Internal Server Error` | 後端在主流程處理過程中發生錯誤，導致本次流程無法完成 |

## 錯誤訊息格式

在 `400 Bad Request`、`404 Not Found` 或 `500 Internal Server Error` 情境下，回應中至少應包含：

- `error_message`
- `error_stage`

若請求缺少 `conversation_id`，應視為請求內容不完整的錯誤情境處理，並回傳對應的最小錯誤資訊。

若已提供 `conversation_id` 但查無對應對話資料，應視為指定資源不存在的錯誤情境處理，並回傳對應的最小錯誤資訊。

## 名詞定義

- `error_message`
  - 本次錯誤的簡短描述。

- `error_stage`
  - 錯誤發生於主流程中的哪一段，例如控制層、`Context Engineering`、`Questioning` 或輸出相關處理。
