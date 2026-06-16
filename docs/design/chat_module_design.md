# Chat Module 設計構想

更新日期時間：2026-06-16 00:00:00

## 文件目的

本文件用於整理 `Chat Module` 的模組定位、責任邊界與控制層路線。此模組的目標，是讓使用者能在已有規劃或任務脈絡下，針對規劃內容、執行方式、學習策略或資源方向進行一般提問，而不必每次都觸發重新規劃或局部修改。

本文件屬於設計層文件，重點在於先收斂模組責任與流程方向；後續若要正式實作，仍需再補資料契約、prompt 規格與測試案例。

---

## 設計背景

目前系統主要支援兩種規劃相關路線：

- 建立第一版規劃
- 修改既有規劃

但使用者在實際使用時，不一定每次後續輸入都是要修改排程。常見情境包括：

- 詢問某個階段應該怎麼做
- 詢問某個任務的練習方向
- 詢問是否有可參考的學習管道或資源
- 要求解釋目前規劃為什麼這樣安排
- 詢問目前規劃是否合理或是否有風險

這些輸入與目前規劃高度相關，但不一定代表使用者要求更新右側排程資料。若全部導入 `Planning Module`，容易造成不必要的重新規劃、局部修改誤判，以及 prompt 規則膨脹。因此需要一條獨立的 `chat` 路線。

---

## 模組定位

`Chat Module` 是一個與任務規劃相關的自然語言回答模組。

它承接 `Context Engineering Module` 整理後的需求資訊、既有規劃摘要與必要對話脈絡，針對使用者提出的規劃相關問題產生 JSON 格式回答。

此模組不負責建立排程、不負責修改排程，也不直接更新 `structured_task_output`。

---

## 責任邊界

### Chat Module 負責

- 回答與目前任務或排程相關的自然語言問題
- 解釋既有規劃中的階段、任務、順序與安排理由
- 提供執行建議、練習方向、注意事項或資源方向
- 根據既有規劃指出可能風險或執行重點
- 產生可由控制層與 Response Module 承接的結構化回答結果

### Chat Module 不負責

- 不建立第一版規劃
- 不修改既有規劃
- 不輸出 `PlanningCreateOutput` 或 `PlanningRevisionOutput`
- 不更新 `structured_task_output`
- 不決定是否需要追問
- 不重新判斷使用者 intent
- 不直接控制主流程分支

---

## 與既有模組的關係

### 與 Context Engineering Module 的關係

`Context Engineering Module` 負責理解本輪輸入與整理上下文，並可標示本輪可能屬於 `create`、`revise`、`chat` 或 `other` 意圖。

CE 可以判斷「使用者正在問第三階段的練習方向」，但不產生實質建議內容。

### 與 Questioning Module 的關係

`Questioning Module` 負責判斷本輪資訊是否足以進入後續路線。

在 `chat` 情境下，Questioning 的重點不是檢查建立排程所需資訊，而是確認是否有足夠回答對象。例如使用者只說「那我要怎麼做」但缺少可指向的任務或階段時，可要求追問；若使用者已明確指定階段或問題內容，則可放行到 Chat Module。

### 與 Planning Module 的關係

`Planning Module` 只處理 `create` 與 `revise`。

若使用者只是詢問建議、解釋或資源方向，應走 Chat Module；只有當使用者明確要求「加入」、「修改」、「重排」、「拆細」等會改變排程資料的行為時，才走 Planning revision。

### 與 Response Module 的關係

`Chat Module` 產生實質回答內容；`Response Module` 只負責包裝或轉換成前端對話區可顯示的文字。

Response Module 不應重新推理一份不同答案，避免形成雙層 AI 回答與內容不一致。

### 與 Persistence Layer 的關係

Chat 回答本身可作為 AI 對話紀錄保存，但不應覆蓋或更新既有結構化排程資料。

---

## Intent 分類方向

後續 `planning_intent.intent_type` 可擴充為：

- `create`：建立新的規劃
- `revise`：修改既有規劃
- `chat`：針對目前任務或規劃提問，但不要求修改排程
- `other`：非規劃相關或目的不明

### 判斷範例

`chat`：

- 第三階段的模擬試題有沒有什麼練習方向？
- 第一階段為什麼要先做基礎建立？
- 這樣安排會不會太趕？
- 有沒有什麼學習管道可以參考？

`revise`：

- 幫我把第三階段加上模擬試題練習方向
- 把第一階段拆得更細
- 第二階段改成每天都有聽力練習
- 幫我重新調整成一週完成

---

## 控制層路線

Chat Module 應作為 Questioning 後的新分支，而不是掛在 Planning Module 內部。

建議控制層路線如下：

```text
F001 Frontend -> Controller
F002 Controller -> Context Engineering + Persistence
F003 Context Engineering -> Questioning
F004 Questioning -> Controller
F005 Controller branch:
  - needs_follow_up -> Response
  - ready + intent=create -> Planning create
  - ready + intent=revise -> Planning revision
  - ready + intent=chat -> Chat Module
  - other/unsafe -> Response follow-up or safe clarification

Planning route:
  Planning -> Output Structuring -> Response -> Controller -> Frontend

Chat route:
  Chat Module -> Response -> Controller -> Frontend
```

在 chat route 中，控制層不應呼叫 Output Structuring Module，也不應更新右側排程面板資料。

---

## Chat Module 輸入方向

第一版可先使用下列資料：

- 本輪使用者原始輸入
- CE 整理後的 requirement context
- CE 判定的 intent 與 target
- conversation history text
- existing plan outline
- 必要時的完整 structured task output

資料庫知識檢索可作為後續擴充，不納入第一版基底。

---

## Chat Module 輸出方向

第一版輸出應維持固定 JSON，避免直接讓 AI 回一段自由文字後難以串接。

建議方向：

```json
{
  "answer_types": [
    "execution_advice",
    "resource_suggestion"
  ],
  "answer": "針對使用者問題產生的回答內容",
  "referenced_plan": {
    "main_task_order": 3,
    "subtask_orders": ["3.1", "3.2"]
  },
  "suggested_follow_up_actions": [
    {
      "action_type": "revise_plan",
      "label": "將這些建議加入第三階段"
    }
  ]
}
```

其中 `suggested_follow_up_actions` 只作為後續互動提示，不代表本輪已修改排程。

---

## 第一版實作邊界

第一版應優先完成：

- 新增 `chat` intent 文件與 schema 設計
- 新增 Chat Module 的 prompt、validator 與 service 骨架
- 控制層新增 chat 分支
- Response Module 可承接 Chat Module output
- 確保 chat route 不會更新 `structured_task_output`
- 增加測試覆蓋典型 chat 與 revise 的分流差異

第一版暫不處理：

- 知識資料庫檢索
- 外部網路查詢
- 多來源引用格式
- 前端快捷操作按鈕

---

## 預期成果

完成 Chat Module 基底後，系統應能做到：

- 使用者針對既有排程提問時，只回答問題，不重做排程
- 使用者明確要求修改時，才進入 revision planning
- Planning Module 的 prompt 不需要承擔一般聊天規則
- Response Module 不需要負責產生業務建議內容
- 控制層能清楚分辨 create、revise、chat 與 follow-up 路線
