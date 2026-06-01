# 輸入至 Planning Create 資料契約

本文件用於定義系統從 `Questioning Module` 放行進入規劃開始，到 `Planning Module` 的 `create planning` 產出初步規劃結果為止的資料契約。

---

## 資料物件一：Planning Create 輸入

### 定義

由前置流程整理完成、可直接提供 `Planning Module` 建立初步規劃的輸入資料。

### 組成內容

- 需求脈絡
- 已知資訊集合
- 待確認資訊集合
- 完整歷史對話內容

### 作用

- 作為 `Planning Module` 建立初步規劃的主要依據
- 保留目前已確認資訊與仍未確認缺口的區別
- 在需要時提供歷史對話背景，幫助 AI 理解本次規劃情境

### 特性

- 此資料物件不負責決定是否應進入規劃
- `known_information` 與 `pending_confirmation` 直接沿用前置模組整理結果
- `conversation_history_text` 現階段作為選用背景，不要求每次皆存在

### 欄位收斂方向

- `requirement_context`
  - 由前置流程整理出的需求摘要，作為本次規劃的主任務背景
- `known_information`
  - 目前可直接採信的資訊集合
- `pending_confirmation`
  - 仍待確認、不可直接視為事實的資訊集合
- `conversation_history_text`
  - 與本次需求相關的完整歷史對話內容

---

## 資料物件二：Planning Create 輸出

### 定義

由 `Planning Module` 的 `create planning` 介面所產出的初步規劃結果。

### 組成內容

- 規劃摘要
- 規劃理由
- 假設資訊集合
- 排程核心結構

### 作用

- 作為控制層後續承接規劃結果的主要資料來源
- 提供 `Output Structuring Module` 產生後續排程輸出時的依據
- 保留規劃理由與假設資訊，支撐可解釋性

### 特性

- `schedule` 為排程核心結構物件
- `structured_task_output` 不直接等於完整 `PlanningCreateOutput`
- 控制層應自 `schedule` 承接排程本體，再交由 `Output Structuring Module` 使用

### 欄位收斂方向

- `plan_summary`
  - 簡要說明本次規劃的整體安排方向
- `design_rationale`
  - 以單一字串說明本次規劃為何這樣安排
- `assumptions_used`
  - 列出本次規劃實際採用的假設資訊；若無則回傳空列表
- `schedule`
  - 排程核心結構物件，內部以 `main_tasks` 為最外層

---

## 與排程核心結構契約的關係

`PlanningCreateOutput.schedule` 的正式欄位定義，應直接依下列文件承接：

- `docs/specs/data_contract/planning_schedule_structure_contract.md`

也就是說：

- `Planning Create 輸出` 定義完整規劃結果的最外層資料
- `planning_schedule_structure_contract.md` 定義 `schedule` 內部的排程核心結構

---

## 資料物件關係

| 階段 | 資料物件之間的關係                            | 說明                                                                                           |
| ---- | --------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 1    | Questioning 判斷結果 -> Planning Create 輸入  | 控制層於 `decision = planning` 時，承接需求摘要與資訊集合，組成 `PlanningCreateInput`         |
| 2    | Planning Create 輸入 -> Planning Create 輸出  | `Planning Module` 依已知資訊、待確認資訊與可選歷史背景，產出初步規劃結果                       |
| 3    | Planning Create 輸出 -> Output Structuring    | 控制層承接 `schedule` 等規劃結果，再交由 `Output Structuring Module` 整理為後續排程輸出資料 |
