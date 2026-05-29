# 對話紀錄資料表實體規格

本文件用於定義對話紀錄資料表的實體欄位結構，對齊目前資料庫 model 與對話資料契約。

---

## 設計原則

- 對外使用的業務識別值與資料庫內部 PK 分離
- `conversation_id` / `turn_id` 提供前端、控制層與持久化契約使用
- `conversation_pk` / `turn_pk` / `message_pk` 僅供資料庫內部關聯與 ORM 使用
- 同一對話內的回合順序由 `turn_index` 表示
- 同一回合內的訊息順序由 `message_index` 表示

---

## 資料表一：`conversations`

### 欄位

- `conversation_pk`
- `conversation_id`
- `title`
- `conversation_history_text`
- `created_at`
- `updated_at`

### 欄位說明

- `conversation_pk`
  - 資料庫內部主鍵。
  - 僅供 ORM relationship 與 FK 關聯使用。

- `conversation_id`
  - 對外使用的對話主體唯一識別值。
  - 由 `Persistence Layer` 建立新對話時生成。
  - 提供前端後續呼叫 `raw_request` 與歷史查詢 API 使用。

- `title`
  - 對話標題。
  - 現階段可為空。

- `conversation_history_text`
  - 聚合後的完整對話歷史文字。
  - 由 `Persistence Layer` 在每次新增 `turn_message` 後同步更新。
  - 主要提供 `Context Engineering Module` 與後續模組直接取得歷史脈絡使用。
  - 原始對話內容仍以 `conversation_turns` 與 `turn_messages` 為正式保存來源。

- `created_at`
  - 對話建立時間。

- `updated_at`
  - 對話最後更新時間。

---

## 資料表二：`conversation_turns`

### 欄位

- `turn_pk`
- `conversation_pk`
- `turn_id`
- `created_at`
- `updated_at`

### 欄位說明

- `turn_pk`
  - 資料庫內部主鍵。

- `conversation_pk`
  - 指向所屬 `conversations.conversation_pk` 的內部 FK。

- `turn_id`
  - 對外使用的單一互動回合唯一識別值。
  - 由持久化層建立新回合時生成。

- `created_at`
  - 本回合建立時間。

- `updated_at`
  - 本回合最後更新時間。

---

## 資料表三：`turn_messages`

### 欄位

- `message_pk`
- `turn_pk`
- `message_index`
- `type`
- `content`
- `created_at`
- `updated_at`

### 欄位說明

- `message_pk`
  - 資料庫內部主鍵。

- `turn_pk`
  - 指向所屬 `conversation_turns.turn_pk` 的內部 FK。

- `message_index`
  - 本訊息在同一回合中的順序。
  - 同一個 `turn_pk` 下不可重複。
  - 現階段雖然常見情況為 user 一筆、ai 一筆，但此欄位先保留，供未來多段 AI chunk、SSE / streaming 或同回合額外 system 訊息時穩定排序使用。

- `type`
  - 訊息角色。
  - 現階段主要對應 `user`、`ai` 與 `system`。

- `content`
  - 訊息文字內容。

- `created_at`
  - 本訊息建立時間。

- `updated_at`
  - 本訊息最後更新時間。

---

## 關聯摘要

- `conversations.conversation_pk` 1 對多 `conversation_turns.conversation_pk`
- `conversation_turns.turn_pk` 1 對多 `turn_messages.turn_pk`

---

## 補充說明

- `conversation_id` 與 `turn_id` 屬於跨層交換時使用的業務識別值
- `conversation_pk`、`turn_pk`、`message_pk` 屬於資料庫內部主鍵，不直接暴露到對外契約
- `conversation_history_text` 屬於聚合後的輔助欄位，用於降低上層模組重組完整歷史文字的成本
