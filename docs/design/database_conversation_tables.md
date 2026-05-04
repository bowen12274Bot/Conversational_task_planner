# Database Conversation Tables — 設計文件

更新時間：2026-05-04

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
| `id` | INTEGER | PK，自動遞增 |
| `title` | TEXT | 對話標題，可為 null |
| `created_at` | DATETIME | 對話建立時間，server default now |
| `updated_at` | DATETIME | 最後更新時間，onupdate now |

---

### `conversation_turns`

| 欄位 | 型別 | 說明 |
|---|---|---|
| `id` | INTEGER | PK，自動遞增 |
| `conversation_id` | INTEGER | FK → `conversations.id` |
| `turn_index` | INTEGER | 本回合在對話中的順序（從 0 開始） |
| `created_at` | DATETIME | 回合建立時間，server default now |
| `updated_at` | DATETIME | 最後更新時間，onupdate now |

---

### `turn_messages`

| 欄位 | 型別 | 說明 |
|---|---|---|
| `id` | INTEGER | PK，自動遞增 |
| `turn_id` | INTEGER | FK → `conversation_turns.id` |
| `role` | TEXT | 訊息角色：`user` / `ai` / `system` |
| `content` | TEXT | 訊息文字內容 |
| `created_at` | DATETIME | 訊息建立時間，server default now |
| `updated_at` | DATETIME | 最後更新時間，onupdate now |

---

## PK / FK 說明

| FK 欄位 | 指向 | ON DELETE |
|---|---|---|
| `conversation_turns.conversation_id` | `conversations.id` | CASCADE |
| `turn_messages.turn_id` | `conversation_turns.id` | CASCADE |

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
  PK id
     title
     created_at
     updated_at
         │
         │ 1 : N
         ▼
conversation_turns
  PK id
  FK conversation_id → conversations.id
     turn_index
     created_at
     updated_at
         │
         │ 1 : N
         ▼
turn_messages
  PK id
  FK turn_id → conversation_turns.id
     role   ("user" | "ai" | "system")
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
