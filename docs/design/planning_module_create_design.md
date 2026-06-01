# Planning Module 建立介面設計

更新日期時間：2026-05-29 00:00:00

本文件用於整理 `Planning Module` 中 `create planning` 介面的設計方向，作為後續撰寫正式規格與安排實作時的依據。

---

## 文件目的

本文件的重點在於說明：

- `create planning` 的責任範圍
- 介面承接哪些上游資料
- 呼叫 AI 前如何整理輸入
- 假設資訊如何處理
- 介面至少應回傳哪些結果

---

## 介面定位

`create planning` 的責任，是在控制層已判定目前可進入規劃分支後，根據已知需求與限制建立一版初步規劃。

此介面不負責：

- 決定是否應進入規劃
- 自行查詢資料庫
- 直接處理前端畫面顯示

此介面負責：

- 承接上游整理好的需求資料
- 將資料整理為 AI 可理解的規劃輸入
- 呼叫 AI 產生規劃結果
- 要求 AI 顯式揭露規劃時使用的假設

---

## 輸入來源

`create planning` 直接承接前面模組已整理好的資料，不額外定義新的上游輸入契約。

目前主要輸入如下：

- `requirement_context`
- `known_information`
- `pending_confirmation`
- `conversation_history_text`

其中：

- `requirement_context`
  - 本次規劃需求的整理後摘要
- `known_information`
  - 目前可直接採信的已知資訊
- `pending_confirmation`
  - 尚未確認、但可能影響規劃精度的資訊
- `conversation_history_text`
  - 與本次需求相關的完整歷史對話內容；現階段可先視為選用資料

---

## 輸入整理原則

呼叫 AI 前，`create planning` 應先將輸入整理成清楚的規劃描述。

整理時至少應遵守以下原則：

- `requirement_context` 作為本次規劃的主任務背景
- `known_information` 作為規劃依據
- `pending_confirmation` 作為待確認缺口，不可直接當成已知事實
- 若 `conversation_history_text` 可取得，則作為補充背景提供給 AI

也就是說，AI 必須能清楚分辨：

- 哪些資訊已知
- 哪些資訊仍待確認
- 哪些地方若要補假設，必須在輸出中揭露

---

## 假設資訊處理原則

本介面允許 AI 在資訊不足但仍可規劃的情況下，採用合理且保守的假設完成初步規劃。

但此行為必須受到以下限制：

- 不可把未提供的資訊直接當成確定事實
- 不可用武斷假設主導整份規劃
- 若使用假設，必須顯式回傳假設內容

假設的目的，是在上游流程已允許進入規劃的前提下，補足少量仍會影響安排的資訊缺口，使系統能產出可展示的初步規劃結果。

---

## AI 任務目標

`create planning` 送交 AI 的任務，至少應包含以下要求：

- 根據目前已知需求與限制產生一版初步規劃
- 優先依據 `known_information` 進行安排
- 對 `pending_confirmation` 只能視為待確認缺口
- 若為完成規劃而採用假設，必須顯式回傳假設內容
- 除了排程結構外，還需回傳規劃摘要與設計理由

---

## 輸出內容

`create planning` 至少應回傳以下內容：

- `plan_summary`
  - 簡要說明本次規劃的整體安排方向
- `design_rationale`
  - 以單一字串說明本次規劃為何這樣安排
- `assumptions_used`
  - 列出本次規劃實際採用的假設資訊；若無假設則回傳空列表
- `schedule`
  - 規劃排程結構物件，內部以 `main_tasks` 為最外層的排程核心結構回傳

其中 `structured_task_output` 並不直接等於完整 `Planning Module` 輸出，而是由控制層承接 `schedule` 後，再交由 `Output Structuring Module` 整理為後續輸出流程使用的排程結構資料。

排程核心結構的正式欄位定義可參考：

- `docs/specs/data_contract/planning_schedule_structure_contract.md`

---

## 模組內部處理責任

在實作層面，`create planning` 可理解為至少包含以下處理段落：

1. 承接 `requirement_context`、`known_information`、`pending_confirmation` 與可選的 `conversation_history_text`
2. 整理成 AI 可理解的規劃任務描述
3. 呼叫 AI 生成規劃結果
4. 驗證 AI 是否回傳規劃摘要、規劃理由、假設資訊與排程結構
5. 將結果交回控制層承接後續輸出流程

---

## MVP 收斂方向

目前 `create planning` 先採以下收斂方向：

- 直接沿用 `Context Engineering Module` 的輸出作為主要上游資料
- 不額外新增新的模組間中介輸入格式
- 允許 AI 在合理範圍內使用假設
- 假設必須顯式輸出
- 排程結構直接依 `planning_schedule_structure_contract.md` 定義輸出

---

## 總結

`Planning Module` 的 `create planning` 介面，目前可先理解為一個承接上游整理結果、將資料轉為 AI 可規劃描述、並產出可解釋初步規劃結果的建立入口。

其核心價值在於：

- 清楚依據目前已知資訊規劃
- 在必要時合理使用假設
- 將假設與規劃理由一併揭露
