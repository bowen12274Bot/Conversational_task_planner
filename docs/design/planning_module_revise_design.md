# Planning Module 修改介面設計

更新日期時間：2026-05-29 00:00:00

本文件用於整理 `Planning Module` 中 `revise planning` 介面的設計方向，作為後續撰寫正式規格與安排實作時的依據。

---

## 文件目的

本文件的重點在於說明：

- `revise planning` 的責任範圍
- 介面承接哪些上游資料
- 呼叫 AI 前如何整理輸入
- 假設資訊如何處理
- 介面至少應回傳哪些結果

---

## 介面定位

`revise planning` 的責任，是在系統已經擁有一份既有規劃的前提下，根據新的修改需求，對原規劃中的局部內容提出調整結果。

目前 MVP 階段先將修改範圍限制在單一主任務內。

此介面不負責：

- 決定是否應進入規劃
- 自行查詢資料庫
- 從零建立完整新規劃
- 直接輸出最終前端顯示格式

此介面負責：

- 承接既有規劃與本次修改需求
- 將資料整理為 AI 可理解的修改輸入
- 呼叫 AI 產生局部修改結果
- 要求 AI 顯式揭露修改時使用的假設

---

## 輸入來源

`revise planning` 除了沿用前面模組已整理的需求資料外，還需承接既有規劃與本次修改需求。

目前主要輸入如下：

- `requirement_context`
- `known_information`
- `pending_confirmation`
- `history_context_summary`
- `existing_plan`
- `revision_request`

其中：

- `requirement_context`
  - 本次規劃需求的整理後摘要
- `known_information`
  - 目前可直接採信的已知資訊
- `pending_confirmation`
  - 尚未確認、但可能影響修改精度的資訊
- `history_context_summary`
  - 與本次修改相關的歷史脈絡內容；現階段可先視為選用資料
- `existing_plan`
  - 目前系統已有的既有規劃或排程結構
- `revision_request`
  - 使用者本次希望修改的內容

---

## 輸入整理原則

呼叫 AI 前，`revise planning` 應先將輸入整理成清楚的修改描述。

整理時至少應遵守以下原則：

- `requirement_context` 作為原規劃目標背景
- `existing_plan` 作為本次修改的基礎資料
- `revision_request` 作為本次修改任務主體
- `known_information` 作為修改依據
- `pending_confirmation` 作為待確認缺口，不可直接當成已知事實
- 若 `history_context_summary` 可取得，則作為補充背景提供給 AI

整份既有排程的最外層結構為 `main_tasks`。本介面目前只處理其中單一 `main_task` 的修改。

---

## 假設資訊處理原則

本介面允許 AI 在資訊不足但仍可完成局部修改的情況下，採用合理且保守的假設。

但此行為必須受到以下限制：

- 不可任意推翻原規劃的主要結構
- 不可把未提供的資訊直接當成確定事實
- 不可因少量資訊不足而重寫整份規劃
- 若使用假設，必須顯式回傳假設內容

假設的目的，是在原規劃大致可延用的前提下，補足少量仍會影響局部修改的資訊缺口。

---

## AI 任務目標

`revise planning` 送交 AI 的任務，至少應包含以下要求：

- 以既有規劃為基礎進行局部修改
- 優先依據 `known_information` 與 `revision_request` 進行調整
- 對 `pending_confirmation` 只能視為待確認缺口
- 若為完成修改而採用假設，必須顯式回傳假設內容
- 除了修改內容外，還需回傳修改摘要與設計理由

---

## 輸出內容

`revise planning` 至少應回傳以下內容：

- `revision_summary`
  - 簡要說明本次修改了哪些方向與整體修改意圖
- `revision_changes`
  - 承接單一主任務範圍內的修改結果
- `design_rationale`
  - 說明本次修改為何這樣安排
- `assumptions_used`
  - 列出本次修改實際採用的假設資訊；若無假設則回傳空列表

`revision_changes` 的細部格式目前暫不固定，但其修改範圍應限制在單一 `main_task` 內。

排程核心結構的正式欄位定義可參考：

- `docs/specs/data_contract/planning_schedule_structure_contract.md`

---

## 模組內部處理責任

在實作層面，`revise planning` 可理解為至少包含以下處理段落：

1. 承接 `requirement_context`、`known_information`、`pending_confirmation`、可選的 `history_context_summary`、`existing_plan` 與 `revision_request`
2. 整理成 AI 可理解的修改任務描述
3. 呼叫 AI 生成局部修改結果
4. 驗證 AI 是否回傳修改摘要、修改理由、假設資訊與修改內容
5. 將結果交回控制層或後續輸出模組承接

---

## MVP 收斂方向

目前 `revise planning` 先採以下收斂方向：

- 直接沿用前面模組已整理好的需求資料
- 額外加入 `existing_plan` 與 `revision_request` 作為修改基礎
- 以局部修改為目標，不重新生成整份完整規劃
- 修改範圍先限制在單一 `main_task` 內
- 允許 AI 在合理範圍內使用假設
- 假設必須顯式輸出
- `revision_changes` 的細部結構待後續再補齊

---

## 總結

`Planning Module` 的 `revise planning` 介面，目前可先理解為一個承接既有規劃與修改需求、將資料轉為 AI 可理解的局部修改描述、並產出可解釋修改結果的更新入口。

其核心價值在於：

- 儘量延續既有規劃結構
- 清楚依據目前已知資訊修改
- 在必要時合理使用假設
- 將假設與修改理由一併揭露
