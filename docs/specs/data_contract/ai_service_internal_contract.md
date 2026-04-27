# AI Service 內部資料契約

本文件用於定義 `AI service layer` 內部在執行 AI 流程時，主要使用的資料物件與其轉接關係。

---

## AI 服務流程起始輸入

### 定義

`AI service layer` 的起始輸入資料直接沿用 [module_to_ai_contract.md](./module_to_ai_contract.md) 中的 `AI 任務請求資料`。

### 作用

- 作為 `service.py` 啟動 AI 流程的起始輸入
- 提供提示建構、模型選擇與 Provider 呼叫所需的原始資料

### 特性

- 此起始輸入直接承接模組層交付的 AI 任務請求
- 此起始輸入不在 AI service layer 內部重新定義新格式

### 名詞定義

- `AI 服務流程起始輸入`
  - `AI 任務請求資料`
  - 實作上對應 `ModuleToAIRequest`

---

## 資料物件一：提示建構輸出資料

### 定義

由 `prompt_builder.py` 依據 AI 服務流程請求資料所建構出的中介資料，用於提供後續 Provider 可直接使用的提示內容與 request payload。

### 組成內容

- 提示內容
- Provider request payload

### 作用

- 將 AI 服務流程請求資料轉為模型可理解的提示內容
- 依不同 Provider 的格式要求，整理成對應的 request payload

### 特性

- 此資料物件屬於 AI service layer 內部中介資料，不直接對外使用
- 此資料物件的重點在於承接提示建構與 Provider 請求格式轉換
- 此資料物件會因 AI Studio 或 OpenRouter 的格式要求而有所差異

### 名詞定義

- `提示內容`
  - 指由 AI 服務流程請求資料整理出的模型輸入文字內容。
- `Provider request payload`
  - 指符合特定 Provider API 格式要求的請求資料內容。

---

## 資料物件二：Provider 執行設定資料

### 定義

由 `config_loader.py` 與 `env_loader.py` 所提供的 Provider 執行設定與憑證資料，用於支援後續對外部 Provider 的呼叫。

### 組成內容

- Provider 識別
- Base URL
- Timeout 秒數
- API Key

### 作用

- 提供對外呼叫 Provider 所需的連線資訊
- 區分靜態設定與私有憑證來源

### 特性

- 此資料物件由 `model_config.yaml` 與 `backend/.env` 共同支撐
- 此資料物件的重點在於執行設定，而不是任務內容本身
- 此資料物件可供不同 Provider client 共用

### 名詞定義

- `Provider 識別`
  - 指本次執行所使用的 Provider 名稱，例如 `ai_studio` 或 `openrouter`。
- `Base URL`
  - 指對外呼叫 Provider API 時所使用的基礎網址。
- `Timeout 秒數`
  - 指單次 Provider 呼叫可等待的最大秒數。

---

## 資料物件三：Provider 呼叫資料

### 定義

由 `service.py` 整理後交付給 `ai_studio_client.py` 或 `openrouter_client.py` 的執行資料，用於完成單次模型呼叫。

### 組成內容

- 模型設定資料
- Provider request payload
- Base URL
- Timeout 秒數
- API Key

### 作用

- 作為單次模型執行所需的完整輸入
- 讓 provider client 可以專注於外部 API 請求與回應解析

### 特性

- 此資料物件同時承接模型設定、提示建構結果與 Provider 執行設定
- 此資料物件的重點在於單次模型呼叫，而不是整段 AI 流程
- 此資料物件會因不同 Provider 而進入不同 client

### 名詞定義

- `模型設定資料`
  - 指本次執行所選定的單一模型設定內容，例如 model name、provider 與 fallback 設定。

---

## Provider 回傳資料

### 定義

由 provider client 在完成單次模型呼叫後回傳的資料，用於提供 `service.py` 判斷本次呼叫成功或失敗。

此資料物件實作上直接沿用 `AIToModuleResult`，不另建立新物件。

### 組成內容

- 是否成功
- 輸出結果
- 錯誤訊息
- 錯誤階段

### 作用

- 作為 `service.py` 判斷是否需要切換備援模型的依據
- 作為 AI service layer 最終回傳結果的基礎

### 特性

- 此資料物件同時用於 AI service layer 內部承接與對外回傳
- 此資料物件的重點在於統一成功與失敗結果格式
- 此資料物件不另於 AI service layer 內部發明新格式

### 名詞定義

- `錯誤階段`
  - 指本次失敗發生於哪一個處理階段，例如 `ai_service_layer`。

---

## 資料物件關係

| 階段 | 資料物件之間的關係 | 說明 |
|---|---|---|
| 1 | `ModuleToAIRequest` -> 提示詞建構輸出資料 | `service.py` 將起始請求交由 `prompt_builder.py` 建構提示詞內容與 request payload |
| 2 | `ModuleToAIRequest` -> Provider 執行設定資料 | `service.py` 依模型與 Provider 取得 base URL、timeout 與 API key |
| 3 | 提示詞建構輸出資料 + Provider 執行設定資料 -> Provider 呼叫資料 | `service.py` 將提示詞建構結果與執行設定整理成單次模型呼叫資料 |
| 4 | Provider 呼叫資料 -> Provider 回傳資料 | provider client 呼叫外部 AI 並回傳 `AIToModuleResult` |
