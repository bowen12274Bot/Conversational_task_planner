# AI 固定格式輸出 API 規格

## 文件名稱

- `ai_structured_output_api`

## API 端點

- 內部串接規格，端點形式待後續實作時定義

## API 目的

- 提供內部模組經由 `AI service layer` 呼叫外部 AI
- 產出固定格式的結構化結果
- 供後端模組後續承接與處理

## 適用範圍

- `Context Engineering Module`
- `Questioning Module`
- `Planning Module`
- `Output Structuring Module`

## 分組方式

- 本 API 已依固定格式輸出用途獨立成一支 API
- 在同一支 API 內，仍可依不同模組用途再做分組
- 不同分組可有不同的輸入格式、輸出格式與處理要求

目前可預期的分組包括：

- `context_for_questioning`
- `questioning_decision`
- `planning_analysis`
- `output_structuring`

### 分組說明

- `context_for_questioning`
  - 用於產出 `Context Engineering Module` 提供給 `Questioning Module` 的固定格式資料，例如需求脈絡、已知資訊集合、待確認資訊集合與歷史脈絡摘要。

- `questioning_decision`
  - 用於一次產出 `Questioning Module` 的固定格式判斷結果，例如是否足以開始規劃、判斷原因、已知資訊集合與待確認資訊集合。

- `planning_analysis`
  - 用於產出 `Planning Module` 的固定格式分析結果，例如拆解完畢的主任務、子任務、估計時間與其他規劃中介資料。

- `output_structuring`
  - 用於產出 `Output Structuring Module` 所需的固定格式結果，作為結構化排程畫面或其他結構化輸出的基礎。

## 輸入內容

- 依分組需求提供對應輸入資料
- 固定格式輸出需求

## 成功條件

- `AI service layer` 成功完成呼叫
- 取得格式正確的資料結構

## 回應訊息

- 成功時，回傳固定格式輸出結果
- 失敗時，回傳錯誤狀態與錯誤資訊

## 狀態碼規範

| 狀態碼 | 名稱 | 說明 |
|---|---|---|
| `200` | `OK` | 本次固定格式輸出請求成功完成 |
| `500` | `Internal Server Error` | AI 串接或固定格式輸出處理過程發生錯誤 |

## 錯誤訊息格式

在錯誤情境下，回應中至少應包含：

- `error_message`
- `error_stage`
