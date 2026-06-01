# Questioning Module 設計構想

更新日期時間：2026-05-30 13:00:00

## 文件目的

本文件用於整理 `Questioning Module` 在目前 MVP 階段的設計方向，說明此模組在整體對話式規劃流程中的責任、輸入與輸出內容，以及目前如何收斂「是否應繼續追問，或可進入規劃」這件事。

本文件屬於設計層文件，重點在於保留設計脈絡與收斂理由；正式規格內容仍以後續 `docs/specs/` 下相關資料契約與流程文件為準。

---

## 設計背景

目前 `Context Engineering Module` 已負責將本輪輸入與歷史脈絡整理為：

- `requirement_context`
- `known_information`
- `pending_confirmation`

但這些整理結果本身仍不足以直接代表「現在是否應該進入規劃」。

原因在於：

- 有些缺口會明顯影響規劃方向，應優先追問
- 有些缺口只會影響規劃精度，不一定需要先問
- 若系統一律追求資訊完整，容易造成過度追問
- 若系統過早放行進入規劃，則可能在關鍵資訊未釐清時產生失真的安排

因此，`Questioning Module` 的角色不是再次抽取資訊，而是站在 `Context Engineering Module` 整理後的結果之上，判斷目前最適合的下一步。

---

## 模組定位

`Questioning Module` 的責任，是根據目前已整理出的需求狀態，決定系統下一步應：

- 繼續追問
- 進入規劃

此模組不負責：

- 重新解析原始使用者輸入
- 重新整理歷史對話內容
- 建立正式規劃結果

此模組負責：

- 讀取目前的需求摘要與已知缺口
- 判斷哪些缺口值得現在追問
- 在資訊不完整但仍可接受時允許進入規劃

也就是說，`Context Engineering Module` 負責「看見並整理資訊」，而 `Questioning Module` 負責「判斷此刻最適合的下一步」。

---

## 核心設計

### 1. 直接承接 `Context Engineering Module` 的整理結果

`Questioning Module` 不重新定義新的需求欄位，而是直接使用前面模組已整理好的資料。

目前主要輸入如下：

- `requirement_context`
- `known_information`
- `pending_confirmation`
- `follow_up_round_count`

其中：

- `requirement_context`
  - 本輪需求與目前狀態的整理後摘要
- `known_information`
  - 已可直接採信的需求資訊
- `pending_confirmation`
  - 尚未確認、但可能影響後續規劃的資訊缺口
- `follow_up_round_count`
  - 與 `conversation` 綁定的追問次數計數器

### 2. 與 `Context Engineering Module` 共用標籤表

為避免不同模組對需求資訊使用不同語言，`Questioning Module` 與 `Context Engineering Module` 共用同一組 requirement labels。

目前共用的標籤如下：

- `task_type`
- `deadline_hint`
- `current_progress`
- `time_budget`
- `difficulty`
- `constraint`

這樣 `Questioning Module` 就可以直接依照 `known_information` 與 `pending_confirmation` 中的既有標籤做判斷，而不必再做額外轉換。

### 3. 以最小規劃基礎與情境型資訊作為判斷依據

目前收斂方向不追求所有資訊補齊後才能規劃，而是先區分：

- 最小規劃基礎
- 情境型資訊

其中目前的最小規劃基礎為：

- `task_type`
- `deadline_hint`

若這兩項資訊仍缺失或不明確，通常不應直接進入規劃。

其餘資訊目前視為情境型資訊：

- `current_progress`
- `time_budget`
- `difficulty`
- `constraint`

這些資訊不一定每次都必須先追問，而是要看它們是否會明顯影響規劃方向或規劃品質。

### 4. 追問的目的在於取得高價值資訊

`Questioning Module` 的設計目標，不是把所有 `pending_confirmation` 都問完，而是判斷哪些缺口值得現在問。

目前收斂原則如下：

- 若缺口會明顯影響規劃方向，應優先追問
- 若缺口只影響規劃精度，不一定要先追問
- 不應為了追求完整而持續補問低價值資訊

因此，`Questioning Module` 本質上是在判斷：

- 現在追問是否仍有價值
- 或目前資訊是否已足以開始初步規劃

### 5. 追問次數與對話狀態綁定

目前規劃將 `follow_up_round_count` 與 `conversation` 綁定，而不是只保留在單次流程內。

其方向如下：

- 每當系統實際進入追問分支一次，計數加一
- 一旦進入規劃分支，計數重置

此設計的目的，是避免系統在多輪對話中無限制地持續追問。

目前收斂方向為：

- `follow_up_round_count` 超過 2 後，不建議再持續追問
- 除非剩餘缺口會使規劃方向明顯失真

---

## 輸出內容

`Questioning Module` 目前先採最小輸出集合，直接服務控制層分支判斷與後續回覆生成。

至少應回傳以下內容：

- `decision`
  - 表示本輪下一步應採取的方向
- `reasoning`
  - 說明為何做出此決策
- `known_information`
  - 本輪可直接沿用的已知資訊
- `pending_confirmation`
  - 本輪仍待確認的資訊
- `next_step_guidance`
  - 以自然語言列出下一步建議內容

其中目前 `decision` 先收斂為：

- `follow_up`
- `planning`

`next_step_guidance` 的內容依 `decision` 而異：

- 若 `decision = follow_up`
  - 內容為下一輪應追問的問題
- 若 `decision = planning`
  - 內容為進入規劃時應如何保守處理剩餘不確定資訊的說明

目前不另外定義 `assumption_candidates` 與 `follow_up_questions` 兩套平行欄位，而是先以同一個 `next_step_guidance` 承接，降低 MVP 階段的複雜度。

---

### Prompt 草案

以下為目前可直接參考的 prompt 組裝格式：

```text
rules:
- 你是規劃前決策助理。
- 你的任務是判斷本輪下一步應該追問，還是進入規劃。
- 與 Context Engineering Module 共用同一組 requirement labels。
- task_type 與 deadline_hint 是規劃前最小基礎。
- current_progress、time_budget、difficulty、constraint 屬於情境型資訊，不是每次都必須追問。
- 不要因為想追求完整而追問所有缺口。
- 只有當缺口會明顯影響規劃方向或品質時，才應追問。
- 若資訊雖不完整，但仍足以形成初步規劃，應允許進入規劃，並在 reasoning 中說明不確定處。
- 若 follow_up_round_count 已超過 2，除非缺口會讓規劃方向明顯失真，否則不建議再繼續追問。

task:
- 讀取 requirement_context、known_information、pending_confirmation 與 follow_up_round_count。
- 判斷下一步是 follow_up 或 planning。
- 若為 follow_up，產出少量高價值追問。
- 若為 planning，說明為何目前資訊已足以開始初步規劃，以及哪些不確定資訊可暫時保留。

context:
- requirement_context
- known_information
- pending_confirmation
- follow_up_round_count

examples:
- input:
    requirement_context: 使用者希望系統協助安排任務，但目前尚未提供明確期限。
    known_information:
      - { "label": "task_type", "value": "Java 作業" }
    pending_confirmation:
      - { "label": "deadline_hint", "question_hint": "預計什麼時候要完成？" }
    follow_up_round_count: 0
  output:
    decision: follow_up
    reasoning: 目前任務內容已知，但期限尚未明確，最小規劃基礎尚未成立，因此應先追問。
    known_information:
      - { "label": "task_type", "value": "Java 作業" }
    pending_confirmation:
      - { "label": "deadline_hint", "question_hint": "預計什麼時候要完成？" }
    next_step_guidance:
      - 預計什麼時候要完成這份 Java 作業？

- input:
    requirement_context: 使用者希望在 7 天內完成 Java 作業，目前主任務與期限已明確。
    known_information:
      - { "label": "task_type", "value": "Java 作業" }
      - { "label": "deadline_hint", "value": "7 天內" }
    pending_confirmation:
      - { "label": "time_budget", "question_hint": "每天大約可投入多少時間？" }
    follow_up_round_count: 1
  output:
    decision: planning
    reasoning: 目前任務內容與期限已足以形成初步規劃，剩餘缺口主要影響規劃精度，因此可先進入規劃。
    known_information:
      - { "label": "task_type", "value": "Java 作業" }
      - { "label": "deadline_hint", "value": "7 天內" }
    pending_confirmation:
      - { "label": "time_budget", "question_hint": "每天大約可投入多少時間？" }
    next_step_guidance:
      - 可先依保守投入時間進行初步規劃，後續若補充每日可投入時間，再調整安排。

- input:
    requirement_context: 使用者希望在 3 天內完成資料庫期末報告，但目前尚不清楚已完成到哪個階段。
    known_information:
      - { "label": "task_type", "value": "資料庫期末報告" }
      - { "label": "deadline_hint", "value": "3 天內" }
    pending_confirmation:
      - { "label": "current_progress", "question_hint": "目前已經完成到哪裡？" }
    follow_up_round_count: 0
  output:
    decision: follow_up
    reasoning: 雖然任務內容與期限已知，但目前進度會明顯影響接下來的安排方式，因此應先追問。
    known_information:
      - { "label": "task_type", "value": "資料庫期末報告" }
      - { "label": "deadline_hint", "value": "3 天內" }
    pending_confirmation:
      - { "label": "current_progress", "question_hint": "目前已經完成到哪裡？" }
    next_step_guidance:
      - 目前這份資料庫期末報告已經完成到哪個階段？

- input:
    requirement_context: 使用者希望在 7 天內完成 Java 作業，但目前需求描述仍偏粗略，尚不清楚作業是剛開始還是已進行一部分。
    known_information:
      - { "label": "task_type", "value": "Java 作業" }
      - { "label": "deadline_hint", "value": "7 天內" }
    pending_confirmation: []
    follow_up_round_count: 0
  output:
    decision: follow_up
    reasoning: 雖然目前沒有顯式待確認項目，但現有情境下進度資訊很可能明顯影響規劃安排，因此仍值得先追問。
    known_information:
      - { "label": "task_type", "value": "Java 作業" }
      - { "label": "deadline_hint", "value": "7 天內" }
    pending_confirmation: []
    next_step_guidance:
      - 目前這份 Java 作業已經完成到哪裡？

format_requirements:
- 輸出必須為 JSON object。
- 必填欄位：
  - decision
  - reasoning
  - known_information
  - pending_confirmation
  - next_step_guidance
- decision 僅可為 follow_up 或 planning。
```

---

## MVP 收斂方向

目前 `Questioning Module` 先採以下收斂方向：

- 直接承接 `Context Engineering Module` 的輸出
- 與 `Context Engineering Module` 共用同一組 requirement labels
- 以 `task_type` 與 `deadline_hint` 作為最小規劃基礎
- 其餘資訊依情境判斷是否值得追問
- `decision` 先只保留 `follow_up` 與 `planning`
- 追問或保守處理建議先統一放入 `next_step_guidance`
- `follow_up_round_count` 與 `conversation` 綁定，用於限制持續追問

---

## 與正式規格的關係

本設計文件後續應對應的正式規格主要包括：

- `docs/specs/data_contract/`
  - `Questioning Module` 的輸入與輸出資料契約

- `docs/specs/data_contract/flow_stage_reference.md`
  - `Questioning Module` 在整體主流程中的節點位置與前後關係

- `docs/specs/module_contract/`
  - 若後續補充 `Questioning Module` 的正式模組介面規格，應以該處為主

若後續實作需要落成正式 schema、Prompt 契約與控制層分支行為，應優先以正式規格文件為準；本文件則保留設計脈絡與目前收斂理由，供後續調整參考。
