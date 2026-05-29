# Database Conversation Tables — 設計文件

更新時間：2026-05-04 19:34:00

---

## 本次任務目標

完成 MVP Phase 2 的對話紀錄資料表建置。  
新增三張 SQLAlchemy 資料表 model，確保 `init_db.py` 可正確建立資料表至 `data/app.db`。  
本次不涉及 API、前端頁面或查詢邏輯。

---

## 三張資料表用途

| 資料表 | 用途 |
|---|---|
| `conversations` | 儲存一整段對話的主資料（對話窗） |
| `conversation_turns` | 儲存一次對話回合（使用者問一次、AI 回一次） |
| `turn_messages` | 儲存每個回合中的實際訊息內容 |

---

## 欄位說明

### `conversations`

| 欄位 | 型別 | 說明 |
|---|---|---|
| `conversation_pk` | INTEGER | 內部 PK，自動遞增 |
| `conversation_id` | STRING(64) | 對外使用的對話識別值，唯一 |
| `title` | TEXT | 對話標題，可為 null |
| `conversation_history_text` | TEXT | 聚合後的完整對話歷史文字，可為 null |
| `created_at` | DATETIME | 對話建立時間，server default now |
| `updated_at` | DATETIME | 最後更新時間，onupdate now |

---

### `conversation_turns`

| 欄位 | 型別 | 說明 |
|---|---|---|
| `turn_pk` | INTEGER | 內部 PK，自動遞增 |
| `conversation_pk` | INTEGER | FK → `conversations.conversation_pk` |
| `turn_id` | STRING(64) | 對外使用的回合識別值，唯一 |
| `created_at` | DATETIME | 回合建立時間，server default now |
| `updated_at` | DATETIME | 最後更新時間，onupdate now |

---

### `turn_messages`

| 欄位 | 型別 | 說明 |
|---|---|---|
| `message_pk` | INTEGER | 內部 PK，自動遞增 |
| `turn_pk` | INTEGER | FK → `conversation_turns.turn_pk` |
| `message_index` | INTEGER | 訊息在同一回合中的順序（從 0 開始） |
| `type` | TEXT | 訊息角色：`user` / `ai` / `system` |
| `content` | TEXT | 訊息文字內容 |
| `created_at` | DATETIME | 訊息建立時間，server default now |
| `updated_at` | DATETIME | 最後更新時間，onupdate now |

---

## PK / FK 說明

| FK 欄位 | 指向 | ON DELETE |
|---|---|---|
| `conversation_turns.conversation_pk` | `conversations.conversation_pk` | CASCADE |
| `turn_messages.turn_pk` | `conversation_turns.turn_pk` | CASCADE |

### 外部 ID 與內部 PK 分離

- `conversation_id` / `turn_id`：對外提供給前端、控制層與持久化契約使用的業務識別值
- `conversation_pk` / `turn_pk` / `message_pk`：僅供資料庫內部關聯與 ORM 使用的主鍵

### `conversation_history_text` 的用途

- `conversation_history_text` 用於保存聚合後的完整對話歷史文字
- 每當新的 `turn_message` 寫入時，應同步更新該 `conversation` 的此欄位
- 此欄位主要提供 `Context Engineering Module` 與後續模組直接讀取歷史脈絡使用
- 原始對話內容仍以 `conversation_turns` 與 `turn_messages` 作為正式保存來源

此設計用於避免將資料庫內部自增主鍵直接暴露到跨層契約中。

### 唯一性與排序規則

- `conversation_id` 必須唯一
- `turn_id` 必須唯一
- 同一個 `turn_pk` 下的 `message_index` 不可重複
- `message_index` 目前先保留，供未來多段 AI chunk、SSE / streaming 或同回合額外 system 訊息時穩定排序使用

---

## 資料表關聯說明

- `Conversation` 1 對多 `ConversationTurn`（一個對話有多個回合）
- `ConversationTurn` 1 對多 `TurnMessage`（一個回合有多筆訊息）
- `TurnMessage` 多對 1 回到 `ConversationTurn`

### SQLAlchemy relationship 摘要

| 物件屬性 | 方向 |
|---|---|
| `Conversation.turns` | → list of `ConversationTurn` |
| `ConversationTurn.conversation` | → parent `Conversation` |
| `ConversationTurn.messages` | → list of `TurnMessage` |
| `TurnMessage.turn` | → parent `ConversationTurn` |

---

## 簡易 ERD（文字版）

```
conversations
  PK conversation_pk
     conversation_id
     title
     conversation_history_text
     created_at
     updated_at
         │
         │ 1 : N
         ▼
conversation_turns
  PK turn_pk
  FK conversation_pk → conversations.conversation_pk
     turn_id
     created_at
     updated_at
         │
         │ 1 : N
         ▼
turn_messages
  PK message_pk
  FK turn_pk → conversation_turns.turn_pk
     message_index
     type   ("user" | "ai" | "system")
     content
     created_at
     updated_at
```

---

## 如何執行資料庫初始化

```powershell
# 從專案根目錄
cd c:\Users\USER\OneDrive\桌面\Conversational_task_planner\backend
python -m app.db.init_db
```

成功輸出範例：

```
✅ Database initialised successfully.
   Tables created: ['conversations', 'conversation_turns', 'turn_messages']
```

資料庫檔案位置：`data/app.db`（相對於專案根目錄）

---

## 如何確認資料表建立成功

### 方法一：Python 快速確認

```powershell
cd c:\Users\USER\OneDrive\桌面\Conversational_task_planner
python -c "import sqlite3; conn=sqlite3.connect('data/app.db'); print(conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall())"
```

預期輸出：

```
[('conversations',), ('conversation_turns',), ('turn_messages',)]
```

### 方法二：SQLite Viewer（VS Code 延伸）

1. 在 VS Code 安裝 `SQLite Viewer` 或 `SQLite` 延伸套件
2. 在檔案總管中點開 `data/app.db`
3. 應可看到三張資料表：`conversations`、`conversation_turns`、`turn_messages`
4. 點擊各表確認欄位名稱與型別是否符合上方規格

### 方法三：確認各表 schema

```powershell
python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
for table in ['conversations', 'conversation_turns', 'turn_messages']:
    print(f'\n=== {table} ===')
    for col in conn.execute(f'PRAGMA table_info({table})').fetchall():
        print(col)
"
```
