# 流程階段參考

本文件用於整理系統主流程的節點關係定義，作為各資料契約文件描述「所在流程階段」時的共用參考。

---

## 文件目的

各資料契約文件在標示所在流程階段時，需要有一份共通的主流程節點關係參考，避免不同文件各自描述而產生不一致。

本文件的重點在於整理系統主流程本身的節點關係。

---

## 流程資料結構

目前系統的主流程，以有向流程圖作為核心結構來保存流程順序、分支關係與節點之間的前後連結。

在此結構中，每個節點都具有：

- 系統識別
- 代號
- 節點名稱
- 處理單位
- 上一步
- 下一步
- 說明

### 系統識別

#### 定義

用於在系統內部穩定指向單一流程節點的識別欄位。

#### 意義

- 每個節點都必須具有唯一的系統識別
- 系統識別建立後，不應因代號、節點名稱或說明調整而任意變更
- 代號與節點名稱主要用於閱讀與辨識
- 系統內部若需要穩定引用節點，應以系統識別為準

### 節點名稱

#### 定義

用於描述節點在流程中所代表之處理關係的可讀名稱欄位。

#### 讀法

節點名稱用於表達「哪一個單位，將流程推向哪一個單位，並完成了什麼動作」。

命名時以小寫英文與底線為原則，優先使用下列寫法：

- 一般節點：`unit_a_to_unit_b_action`
- 同一單位內節點：`unit_action`
- 分支節點擇一傳送：`unit_a_to_unit_b_or_unit_c_branch`
- 分支節點同時傳送：`unit_a_to_unit_b_and_unit_c_dispatch`

其中：

- `unit_a` 表示主要來源單位
- `unit_b` 表示主要目標單位
- `action` 表示此節點的主要處理動作
- 若為分支節點擇一傳送，動作統一使用 `branch`
- 若為分支節點同時傳送，動作可使用 `dispatch`

---

## 流程關係圖

以下表格作為目前主流程的流程關係圖定義基準。

在 MVP 階段，本文先定義追問路線、規劃路線與規劃相關問答路線；後續若有新分支或新節點，應延續同一份流程資料結構擴充。

目前除主流程外，也補充以下與對話紀錄相關的流程：

- 建立對話路線
- 對話紀錄存入路線
- 歷史對話紀錄查詢路線

| 系統識別 | 代號 | 節點名稱 | 處理單位 | 上一步 | 下一步 | 說明 |
|---|---|---|---|---|---|---|
| `F013` | `N13` | `controller_to_persistence_conversation_create_transfer` | 後端流程控制層 -> `Persistence Layer` | 開始 | `N14` | 前端初始化請求建立新對話時，控制層將建立對話需求送入 `Persistence Layer`。 |
| `F014` | `N14` | `persistence_to_controller_conversation_create_return` | `Persistence Layer` -> 後端流程控制層 | `N13` | 結束 | `Persistence Layer` 已建立新對話並生成對話識別值，因此將結果交回控制層承接。 |
| `F001` | `N1` | `frontend_to_controller_submit` | 前端介面層 -> 後端流程控制層 | 開始 | `N2` | 使用者已提交需求，因此流程由前端進入控制層。 |
| `F002` | `N2` | `controller_to_context_engineering_transfer_and_persistence_store` | 後端流程控制層 -> `Context Engineering Module` 與 `Persistence Layer` | `N1` | `N3` 與 結束 | 控制層承接使用者輸入後，會同步將主流程資料轉交給 `Context Engineering Module`，並將使用者端對話紀錄資料送入 `Persistence Layer` 保存。 |
| `F003` | `N3` | `context_engineering_to_questioning_prepare` | `Context Engineering Module` -> `Questioning Module` | `N2` | `N4` | 已取得可用資訊基礎，因此可交由 `Questioning Module` 判斷資訊是否足夠。 |
| `F004` | `N4` | `questioning_to_controller_evaluate` | `Questioning Module` -> 後端流程控制層 | `N3` | `N5` | `Questioning Module` 已完成判斷，因此控制層可依該結果決定後續分支。 |
| `F005` | `N5` | `controller_to_response_or_planning_or_chat_branch` | 後端流程控制層 -> `Response Module`、`Planning Module` 或 `Chat Module` | `N4` | `N6`、`N8` 或 `N19` | 若 `Questioning Module` 判斷需要追問，則進入 `Response Module`；若判斷資訊已足以建立或修改規劃，則進入規劃相關處理；若本輪屬於規劃相關問答，則進入 `Chat Module`。 |
| `F006` | `N6` | `response_to_controller_return_and_persistence_store` | `Response Module` -> 後端流程控制層與 `Persistence Layer` | `N5` | `N7` 與 結束 | `Response Module` 已將追問文字準備完成，因此會同步將結果交回控制層承接前端回傳路線，並將 AI 端對話紀錄資料送入 `Persistence Layer` 保存。 |
| `F007` | `N7` | `controller_to_frontend_return` | 後端流程控制層 -> 前端介面層 | `N6` | 結束 | 本輪結果屬於追問或規劃相關問答情境，控制層將內容送回前端並結束本輪主流程。 |
| `F008` | `N8` | `planning_to_controller_return` | `Planning Module` -> 後端流程控制層 | `N5` | `N9` | `Planning Module` 已完成中介規劃分析，因此先將規劃結果交回控制層承接。 |
| `F009` | `N9` | `planning_to_output_structuring_and_response_dispatch` | 後端流程控制層 -> `Output Structuring Module` 與 `Response Module` | `N8` | `N10` 與 `N11` | 控制層承接 `Planning Module` 的規劃結果後，會將同一份規劃基礎資料以同步派送狀態同時送入 `Output Structuring Module` 與 `Response Module`。 |
| `F010` | `N10` | `output_structuring_to_controller_return` | `Output Structuring Module` -> 後端流程控制層 | `N9` | `N12` | `Output Structuring Module` 已完成結構化結果，因此先將資料交回控制層承接。 |
| `F011` | `N11` | `response_to_controller_return` | `Response Module` -> 後端流程控制層 | `N9` | `N12` | `Response Module` 已根據 `Planning Module` 的規劃結果完成文字輸出，因此先將本輪文字內容交回控制層承接。 |
| `F012` | `N12` | `controller_to_frontend_return` | 後端流程控制層 -> 前端介面層 | `N10` 或 `N11` | 結束 | 控制層整合結構化結果與文字回覆後，將規劃情境下的內容送回前端並結束流程。 |
| `F015` | `N15` | `frontend_to_controller_conversation_history_request` | 前端介面層 -> 後端流程控制層 | 開始 | `N16` | 前端請求既有對話的歷史紀錄，因此流程先由前端進入控制層。 |
| `F016` | `N16` | `controller_to_persistence_conversation_history_transfer` | 後端流程控制層 -> `Persistence Layer` | `N15` | `N17` | 控制層承接歷史查詢請求後，將指定對話的歷史查詢需求送入 `Persistence Layer`。 |
| `F017` | `N17` | `persistence_to_controller_conversation_history_return` | `Persistence Layer` -> 後端流程控制層 | `N16` | `N18` | `Persistence Layer` 已完成歷史對話紀錄查詢與打包，因此將歷史對話資料交回控制層承接。 |
| `F018` | `N18` | `controller_to_frontend_conversation_history_return` | 後端流程控制層 -> 前端介面層 | `N17` | 結束 | 控制層承接歷史對話資料後，將內容回傳前端，用於重建對話畫面。 |
| `F019` | `N19` | `controller_to_chat_transfer` | 後端流程控制層 -> `Chat Module` | `N5` | `N20` | 控制層判定本輪屬於規劃相關問答，且不應建立或修改排程，因此將上下文、既有規劃摘要與本輪問題交給 `Chat Module`。 |
| `F020` | `N20` | `chat_to_response_return_and_persistence_store` | `Chat Module` -> `Response Module` -> 後端流程控制層與 `Persistence Layer` | `N19` | `N7` 與 結束 | `Chat Module` 已完成 JSON 回答結果，因此交由 `Response Module` 包裝成前端對話區可顯示的文字，並將 AI 端對話紀錄資料送入 `Persistence Layer` 保存。此路線不進入 `Output Structuring Module`，也不更新結構化排程資料。 |

---

## 使用方式

若某份資料契約文件需要標示其所在流程階段，可引用本文件中的流程資料結構與流程關係圖，指出該契約位於主流程中的哪一個節點或哪一段關係。
