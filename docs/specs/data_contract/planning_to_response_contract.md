# 輸入至 Planning Response 資料契約

本文件用於定義系統從 `Planning Module` 完成初步規劃之後，到 `Response Module` 生成左側聊天區最終規劃回覆文字為止的資料契約。

---

## 資料物件：Planning Response 輸入

### 定義

由控制層在 `Planning Module` 與 `Output Structuring Module` 完成後，整理並提供給 `Response Module` 用來生成規劃完成回覆文字的輸入資料。

### 組成內容

- 規劃摘要
- 規劃理由
- 結構化排程輸出

### 作用

- 讓 `Response Module` 根據已完成的規劃結果，生成適合顯示於聊天區的簡短自然語言回覆
- 將規劃內容本體與聊天區回覆責任拆開
- 避免控制層直接使用 `plan_summary` 當成最終回覆文字

### 特性

- 此資料物件不負責排程內容生成
- 此資料物件只用於生成規劃完成後的簡短文字回覆
- `structured_task_output` 已代表右側規劃面板的主要顯示內容，因此 `Response Module` 不需重新生成排程本體

### 欄位收斂方向

- `plan_summary`
  - 作為本次規劃整體安排方向的主要摘要來源
- `design_rationale`
  - 用於補充本次規劃為何如此安排
- `structured_task_output`
  - 用於讓 `Response Module` 知道右側規劃面板已承接哪些內容，避免回覆與面板脫節

---

## 與 Response 輸出契約的關係

- 本文件定義的是 `Response Module` 在 planning 路徑下的輸入資料
- `Response Module` 的統一對外輸出格式，仍應依下列文件承接：
  - [response_to_controller_contract.md](./response_to_controller_contract.md)

也就是說：

- `Planning Response 輸入`
  - 定義 `Response Module` 在 planning 路徑中要吃什麼
- `Response 輸出資料契約`
  - 定義 `Response Module` 最後交回控制層的純文字回覆格式

---

## 資料物件關係

| 階段 | 資料物件之間的關係                               | 說明                                                                                           |
| ---- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| 1    | Planning Create 輸出 -> Output Structuring 輸出  | `Planning Module` 先產出完整規劃，再由 `Output Structuring Module` 整理為右側規劃顯示資料     |
| 2    | Planning Create 輸出 + Structured Task Output -> Planning Response 輸入 | 控制層承接 `plan_summary`、`design_rationale` 與 `structured_task_output`，組成 planning 路徑的 response 輸入 |
| 3    | Planning Response 輸入 -> Response 輸出資料      | `Response Module` 生成純文字的規劃完成回覆，供聊天區顯示                                      |
