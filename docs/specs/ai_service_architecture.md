# AI Service Architecture

更新時間：2026-04-26 13:24:00

本文件定義 `AI service layer` 的架構角色、分工與對外關係。

本文件屬於架構層級規範，不展開資料契約、API 細節與設計歷程。

## 文件目的

本文件用於建立 `AI service layer` 的架構共識，內容包含：
- 系統中的架構定位
- 與模組層及外部 Provider 的關係
- 內部分工與核心功能
- Provider 與模型的使用方式

## 架構定位

`AI service layer` 位於模組層與外部 AI Provider 之間，作為模組層使用外部 AI 的統一入口。

模組層不直接呼叫外部 Provider，而是透過 `service.py` 啟動 `AI service layer`。`AI service layer` 負責選擇模型、組裝提示詞與 request payload、呼叫 Provider，並將回應整理為系統內部的統一結果。

`AI service layer` 不負責：
- 業務流程判斷
- 控制層流程轉移決策
- 模組內部業務邏輯

流程控制仍由控制層與模組層負責。

## 分工總覽

目前 `AI service layer` 相關程式與設定檔如下：

- 程式入口路徑：`backend/app/services/ai_service/`

- `service.py`
  - `AI service layer` 的主流程協調入口
  - 負責模型選擇、模型鏈建立、單一模型執行與整體 AI 流程執行

- `model_config.yaml`
  - `AI service layer` 的靜態設定檔
  - 定義 Provider 設定與模型設定

- `backend/.env`
  - 本機私有環境變數檔
  - 放置個人 Provider API key

- `backend/.env.example`
  - 環境變數模板
  - 用於說明專案需要哪些 API key

- `prompt_builder.py`
  - 將模組層送來的請求資料轉為 Provider 可使用的 prompt / request payload

- `config_loader.py`
  - 讀取 `model_config.yaml`
  - 提供 Provider base URL 與 timeout 設定讀取功能

- `env_loader.py`
  - 讀取本機環境變數與 `backend/.env`
  - 取得 Provider API key

- `clients/ai_studio_client.py`
  - AI Studio 的 Provider client
  - 負責送出請求與解析回應

- `clients/openrouter_client.py`
  - OpenRouter 的 Provider client
  - 負責送出請求與解析回應

## 核心功能

`AI service layer` 的核心功能可以直接理解成一段固定流程。

### 1. 接收模組請求

模組先整理好 AI 任務內容，再交給 `AI service layer`。`AI service layer` 只負責接手執行，不回頭決定模組原本要做什麼任務。

### 2. 選擇起始模型

`AI service layer` 會根據請求中的 `capability_level`，選出這次任務要先使用的起始模型。依照`default` 與 `strong`的能力等級劃分使用的模型 。

### 3. 建立模型鏈

選定起始模型後，`AI service layer` 會依照模型設定中的 `fallback_to` 建立模型鏈。這條鏈用來定義主模型與備援模型的嘗試順序。

### 4. 組裝提示內容與 Provider Payload

`AI service layer` 會把模組請求整理成可供模型使用的提示內容，並依不同 Provider 的格式要求，組裝成對應的 request payload。這部分由 `prompt_builder.py` 負責。

### 5. 載入 Provider 設定與金鑰

在真正呼叫外部 AI 之前，`AI service layer` 會先讀取該 Provider 所需的設定與憑證。靜態設定來自 `model_config.yaml`，例如 `base_url` 與 `timeout_seconds`；私有金鑰則來自 `backend/.env`。

### 6. 呼叫外部 AI Provider

`AI service layer` 會把已完成的 payload 交給對應的 provider client，由 client 負責發送請求、接收回應，並處理 Provider 回傳的原始資料。

### 7. 失敗時切換備援

如果目前模型執行失敗，`AI service layer` 會依模型鏈改用下一個模型繼續嘗試。現行規則為同一能力等級下，優先使用 AI Studio，失敗後再切換至 OpenRouter。

### 8. 回傳統一結果

不論最終成功或失敗，`AI service layer` 都會把結果整理成系統內統一的回傳格式，再交還給模組層，讓後續流程不需要直接面對不同 Provider 的差異。

## Provider

目前 `AI service layer` 支援以下 Provider：

### AI Studio

AI Studio 為 Google 提供的生成式 AI 服務介面，可直接使用 Google 提供的模型。本系統將 AI Studio 作為主要 Provider 使用，優先承接 `default` 與 `strong` 能力等級的模型執行。

### OpenRouter

OpenRouter 為聚合式 AI Provider 入口，可透過單一介面連接多個模型來源。本系統將 OpenRouter 作為備援 Provider 使用，當主線 Provider 執行失敗時承接 fallback 模型執行。

## AI 模型

目前模型使用以 `capability_level` 區分，並由不同 Provider 提供對應模型。

### default

- AI Studio：`gemma-3-12b-it`
- OpenRouter：`google/gemma-3-12b-it`

### strong

- AI Studio：`gemma-4-26b-a4b-it`
- OpenRouter：`google/gemma-4-26b-a4b-it`

同一 `capability_level` 下，AI Studio 為主，OpenRouter 為備援，實際切換順序由 `fallback_to` 定義。

## 其他 AI 規範文件參考

本文件對應之其他 AI 規範文件如下：

- `docs/specs/data_contract/module_to_ai_contract.md`
  - 定義模組層與 `AI service layer` 之間的資料契約

- `docs/specs/data_contract/ai_service_internal_contract.md`
  - 定義 `AI service layer` 內部資料物件與資料流向

- `docs/specs/api_spec/ai_text_output_api.md`
  - 定義文字輸出型 AI API 規格

- `docs/specs/api_spec/ai_structured_output_api.md`
  - 定義結構化輸出型 AI API 規格

- `docs/ai_usage_guide.md`
  - 提供組員設定 API key、本機環境與接通測試的操作說明
