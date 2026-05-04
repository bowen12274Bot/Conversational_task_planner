# 對話紀錄資料表草稿

## 資料表一：`conversations`

### 最小欄位

- `conversation_id`
- `created_at`

### 欄位說明

- `conversation_id`
  - 對話主體的唯一識別值。
  - 由 `Persistence Layer` 建立新對話時生成。
  - 提供前端後續呼叫 `raw_request` 與歷史紀錄 API 使用。

- `created_at`
  - 對話建立時間。

---

## 資料表二：`conversation_turns`

### 最小欄位

- `turn_id`
- `conversation_id`
- `created_at`

### 欄位說明

- `turn_id`
  - 單一互動回合的唯一識別值。

- `conversation_id`
  - 指向所屬的 `conversation`。

- `created_at`
  - 本回合建立時間。

---

## 資料表三：`turn_messages`

### 最小欄位

- `message_id`
- `turn_id`
- `type`
- `content`
- `created_at`

### 欄位說明

- `message_id`
  - 單筆訊息的唯一識別值。

- `turn_id`
  - 指向所屬的 `turn`。

- `type`
  - 訊息角色。
  - 現階段主要對應 `user`、`ai` 與 `system`。

- `content`
  - 訊息文字內容。

- `created_at`
  - 本訊息建立時間。
