# 輸入至 Questioning 資料契約

本文件用於定義系統從使用者輸入需求開始，到 `Questioning Module` 產出判斷結果為止的前置鏈路資料契約。

---

## 資料物件一：原始需求輸入

### 定義

使用者提交的原始自然語言需求，作為整個流程的起點。

### 作用

- 保留使用者最原始的表達內容
- 作為 `Context Engineering Module` 的分析依據

### 特性

- 以使用者原句為核心
- 不要求在此階段完成結構化整理
- 不在此階段判斷資訊是否足夠

---

## 資料物件二：Context Engineering 整理結果

### 定義

由 `Context Engineering Module` 根據原始需求與歷史脈絡內容整理出的可用資訊基礎。

### 組成內容

- 需求脈絡
- 已知資訊集合
- 待確認資訊集合
- 歷史脈絡內容
- 追問次數計數器

### 作用

- 將原始需求轉為後續模組可使用的資訊
- 提供 `Questioning Module` 作為判斷基礎

### 特性

- 是整理結果，不是判斷結果
- `已知資訊集合` 與 `待確認資訊集合` 都屬於此資料物件的一部分
- `歷史脈絡內容` 現階段主要由 `Persistence Layer` 維護的 `conversation_history_text` 提供
- `Context Engineering Module` 現階段先直接使用該歷史內容，不額外要求先產生獨立摘要
- `追問次數計數器` 與 `conversation` 綁定，用於幫助 `Questioning Module` 判斷是否仍適合持續追問

### 名詞定義

- `需求脈絡`
  - 由 AI 根據原始輸入整理出的需求理解文字，用於抓住使用者需求中的核心脈絡，降低原始描述過於模糊而無法進一步分析的情況。

- `已知資訊集合`
  - 從需求中辨識出的、對排程規劃屬於必要且目前可直接使用的資訊集合。

- `待確認資訊集合`
  - 從需求中辨識出的、可能影響規劃但仍存在模糊空間或隱含表達、尚不適合直接採用的資訊集合。

- `歷史脈絡內容`
  - 用於補充與目前需求相關的既有互動或背景脈絡，幫助後續模組取得較完整的理解基礎。現階段主要來源為 `conversation_history_text`。

- `追問次數計數器`
  - 用於記錄目前對話已實際進入追問分支的次數。每次系統進入追問回覆時計數加一，一旦流程進入規劃則重置。

---

## 資料物件三：Questioning 判斷結果

### 定義

由 `Questioning Module` 根據 `Context Engineering` 整理結果所產出的判斷資料。

### 組成內容

- 下一步決策
- 判斷原因
- 已知資訊集合
- 待確認資訊集合
- 下一步建議內容

### 作用

- 提供流程控制層決定下一步應進入追問或規劃
- 提供後續模組沿用已知資訊與待確認資訊
- 作為 `Response Module` 在追問情境下生成回覆的直接輸入
- 作為後續規劃流程理解目前剩餘不確定處的依據

### 特性

- 目前以 `decision` 直接表示下一步應採取的方向
- `decision` 現階段僅收斂為：
  - `follow_up`
  - `planning`
- 仍屬於 `Questioning Module` 的輸出，不負責定義 `Response Module` 的對外輸出格式
- `next_step_guidance` 以自然語言列表承接下一步建議內容
- 若 `decision = follow_up`
  - `next_step_guidance` 應提供下一輪應追問的問題
- 若 `decision = planning`
  - `next_step_guidance` 應提供進入規劃時如何保守處理剩餘不確定資訊的說明

### 欄位收斂方向

- `decision`
  - 目前先不再使用「是否足以開始規劃」的布林表示法，而直接用下一步決策承接控制層分支判斷

- `reasoning`
  - 用於說明為何目前應追問或可進入規劃
  - 若資訊不完整但仍允許規劃，也應在此欄位明確揭露理由

- `known_information`
  - 由 `Questioning Module` 直接沿用或整理後回傳，供後續模組延用

- `pending_confirmation`
  - 表示目前仍待確認的需求缺口

- `next_step_guidance`
  - 以自然語言列表承接下一步建議內容
  - 現階段不另外拆分為 `follow_up_questions` 或 `assumption_candidates`

---

## Questioning 判斷原則

`Questioning Module` 的判斷，不以追求所有資訊補齊為目標，而是判斷目前是否仍值得追問。

目前收斂方向如下：

- `task_type` 與 `deadline_hint` 為最小規劃基礎
- 若上述基礎資訊缺失或不明確，通常應優先追問
- `current_progress`、`time_budget`、`difficulty`、`constraint` 視為情境型資訊
- 情境型資訊不一定都必須先問，而是依其對規劃方向與規劃品質的影響決定
- `follow_up_round_count` 偏高時，除非剩餘缺口會使規劃方向明顯失真，否則不應持續追問

---

## 資料物件關係

| 階段 | 資料物件之間的關係                                   | 說明                                                                                                                                  |
| ---- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | 原始需求輸入 -> Context Engineering 整理結果         | `Context Engineering Module` 以原始需求為基礎，整理出可供後續模組使用的資訊                                                           |
| 2    | Context Engineering 整理結果 -> Questioning 判斷結果 | `Questioning Module` 根據整理結果與追問次數，判斷下一步應追問或進入規劃                                                               |
| 3    | Questioning 判斷結果 -> 後續模組                     | `QuestioningDecision` 會保留 `已知資訊集合`、`待確認資訊集合` 與 `next_step_guidance`，供控制層、`Response Module` 與後續規劃流程延用 |
