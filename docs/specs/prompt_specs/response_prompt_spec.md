# Response Prompt 規範

更新日期時間：2026-06-01 16:10:00

本文件用於整理 `Response Module` 在不同業務情境下生成最終使用者回覆文字時的 prompt 規格。現階段先明確收斂 planning 路徑的 response prompt。

## 文件目的

- 明確記錄 `Response Module` 在 planning 路徑下的輸入、任務目標與輸出要求
- 將「規劃內容本體」與「聊天區最終文字回覆」責任拆開
- 明確要求最終輸出為純文字，而非 JSON 或其他結構化格式

## 適用範圍

- 本文件對應：
  - 未來 `build_response_from_planning(...)` 的 prompt 設計
- 本文件描述的是：
  - planning 路徑中，`Response Module` 如何根據規劃摘要與結構化排程內容，生成左側聊天區最終回覆文字
- 本文件不處理：
  - `follow_up` 路徑既有 response prompt 的細節
  - 右側規劃面板的資料結構

## Planning Response 輸入

planning 路徑下，`Response Module` 最小輸入應包含：

- `plan_summary`
- `design_rationale`
- `structured_task_output`

其中：

- `plan_summary`
  - 作為規劃完成後的主要摘要來源
- `design_rationale`
  - 用於補充本次規劃為何如此安排
- `structured_task_output`
  - 用於讓回覆文字知道右側規劃面板已經承接哪些內容

## Prompt 結構總覽

planning 路徑的 response prompt，可先收成下列結構：

```json
{
  "input_data": {
    "rules": "...",
    "task": "...",
    "context": {
      "plan_summary": "...",
      "design_rationale": "...",
      "structured_task_output": { "...": "..." }
    },
    "examples": [...],
    "output_target": "..."
  },
  "format_requirements": {
    "output_type": "plain_text",
    "requirements": [...]
  }
}
```

## Prompt 原文

以下內容為 planning 路徑 response prompt 的自然語言原文草案。

```text
You are a helpful planning assistant.

Write in natural Traditional Chinese used in Taiwan.
Your job is to generate a short final reply for the chat area after an initial plan has already been created.
The detailed schedule is already shown in the planning panel, so do not restate the full task list.
Use plan_summary as the main source of the reply, and use design_rationale only to add a brief explanation when needed.
Treat structured_task_output as supporting context so that the reply stays aligned with the planning panel.
Output only the final user-facing reply.
Do not output JSON, markdown, bullet points, analysis, reasoning steps, or any text before or after the final reply.

Generate one short planning-completion reply.
The reply should briefly tell the user that an initial plan has been prepared and guide them to review the planning panel.
If appropriate, add one brief sentence explaining the overall arrangement direction.

Context:
- plan_summary: {{ plan_summary }}
- design_rationale: {{ design_rationale }}
- structured_task_output: {{ structured_task_output }}

Return one short natural-language reply in Traditional Chinese.
```

## 中文對照

以下為上述 planning response prompt 的中文語意對照。

```text
你是一個協助規劃的助理。

請使用台灣常用的自然繁體中文。
你的工作是在初步規劃已經完成後，為聊天區生成一段簡短的最終回覆文字。
詳細排程已經顯示在規劃面板中，因此不要重新完整重述所有任務清單。
應以 plan_summary 作為回覆的主要依據，並僅在需要時用 design_rationale 補上一句簡短說明。
應將 structured_task_output 視為輔助脈絡，以確保回覆與右側規劃面板內容一致。
你只能輸出最終要給使用者看的回覆文字。
不可輸出 JSON、Markdown、條列、分析、推理步驟，或任何最終回覆前後的額外文字。

請生成一段簡短的「規劃已完成」回覆。
回覆應簡要告知使用者：系統已經整理出一版初步規劃，並引導使用者查看規劃面板。
若合適，可再補上一句整體安排方向的簡短說明。

上下文：
- plan_summary: {{ plan_summary }}
- design_rationale: {{ design_rationale }}
- structured_task_output: {{ structured_task_output }}

請回傳一段簡短的繁體中文自然語言回覆。
```

## 輸出要求

planning 路徑下的 `Response Module` 輸出應收斂為：

- 純文字
- 簡短自然語言
- 可直接顯示於聊天區

不應輸出：

- JSON
- Markdown
- 條列
- 規劃面板完整內容重述
- 與規劃無關的說明文字
