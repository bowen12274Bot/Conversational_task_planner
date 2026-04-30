# 對話歷史紀錄 API 規格

## 文件名稱

- `conversation_history_api`

## API 端點

- `GET /api/conversations/{conversation_id}/history`

## API 目的

- 提供前端於初始化或頁面刷新後讀取既有對話歷史紀錄
- 讓前端可依回傳結果重建本地 message cache
- 作為控制層向 `Persistence Module` 取得歷史資料後，回傳前端的外部查詢接口

## 輸入內容

- 路徑參數 `conversation_id`

## 成功條件

- 指定 `conversation_id` 存在
- 後端成功自持久化資料中取得該對話的歷史資料
- 回應資料足以讓前端重建對話顯示所需內容

## 回應訊息

- 成功時，回傳指定對話的歷史 `turn` 與 `message` 資料
- 失敗時，回傳錯誤狀態與最小錯誤資訊

## 最小回應資料

- `conversation_id`
- `turns`

其中：

- `conversation_id`
  - 指目前查詢的對話識別值。

- `turns`
  - 指本次回傳的歷史回合資料列表。

每個 `turn` 應包含其對應的 `message` 資料。

本 API 目前僅要求回應資料中具備：

- `turn`
- `message`

至於 `turn` 與 `message` 的詳細欄位內容，後續再由資料契約文件定義。

## 狀態碼

| 狀態碼 | 名稱 | 說明 |
|---|---|---|
| `200` | `OK` | 成功取得指定對話的歷史紀錄，且回傳資料足以供前端重建畫面 |
| `400` | `Bad Request` | 請求內容不符合基本要求，例如 `conversation_id` 格式不正確 |
| `404` | `Not Found` | 指定 `conversation_id` 不存在，或查無可讀取的對話資料 |
| `500` | `Internal Server Error` | 後端在查詢歷史紀錄或整理回應資料時發生錯誤 |

## 錯誤訊息格式

在 `400`、`404` 或 `500` 情境下，回應中至少應包含：

- `error_message`
- `error_stage`

## 名詞定義

- `error_message`
  - 本次錯誤的簡短描述。

- `error_stage`
  - 錯誤發生的處理位置，例如控制層、`Persistence Module` 或回應整理階段。

- `turn`
  - 指一次互動回合，作為同一組 user / assistant / system 訊息的保存單位。

- `message`
  - 指某一個 `turn` 內所包含的歷史訊息資料。
