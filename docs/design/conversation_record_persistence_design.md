# 對話紀錄保存設計構想

更新日期時間：2026-05-01 14:27:00

## 文件目的

本文件用於整理 MVP2 階段對話紀錄保存功能的設計想法，說明目前為何需要建立固定的對話識別值、如何保存每次使用者輸入，以及歷史資料應如何回傳。

本文件屬於設計層文件，重點在於保留設計脈絡與收斂理由；正式規格內容仍以 `docs/specs/` 下相關 API、資料契約與資料表文件為準。

---

## 設計背景

目前前端已具備基本對話畫面與即時顯示能力，但若對話資料只停留在前端記憶體中，會出現幾個明顯問題：

- 頁面刷新後，既有對話內容會消失
- 後端無法在後續流程中引用先前對話內容
- 未來若要進入規劃流程，缺少可回溯的歷史脈絡

因此，MVP2 需要補上最小可用的對話紀錄保存能力，讓目前的對話內容不只顯示在前端，也能正式進入持久化流程。

---

## 核心設計

### 1. 先建立固定的 `conversation_id`

`conversation_id` 的作用，是用來識別單一對話窗所屬的對話主體。

這裡之所以需要先建立 `conversation_id`，是因為考量後續設計上需要保留「有多組對話」的空間。

因此目前的收斂方向是：

- 先以 `conversations` 作為對話窗單位
- 每一個對話窗對應一個 `conversation`
- 每一個 `conversation` 具有自己的 `conversation_id`

這樣做的好處是，即使目前 MVP2 階段只先支撐最小對話保存能力，後續若前端需要承接多組對話、切換不同對話窗，或讓不同歷史對話各自保存與重建，也不需要回頭重做整個定位方式。

因此目前收斂的方向是：

- 前端初始化時先呼叫建立對話 API
- 後端建立新的 `conversation`
- `Persistence Layer` 生成並保存 `conversation_id`
- 前端取得 `conversation_id` 後，保存於本地狀態與可重載的前端儲存位置

這樣後續不論是送出對話內容或查詢歷史紀錄，都能以同一個 `conversation_id` 作為定位基礎。

### 2. 每輪對話都要保存使用者端與 AI 端資料

對話紀錄保存不能只保留單一側內容，而是需要讓每一輪互動至少留下：

- 一次使用者輸入
- 一次 AI 回覆

這樣之後查回的歷史資料才是完整的，也才能支撐前端重建畫面與後續流程引用。

目前的方向是：

- 前端送出一次對話內容
- 後端控制層承接本次輸入
- 在主流程進入 `Context Engineering` 的同時，控制層也將本次使用者端資料送入 `Persistence Layer`
- `Response Module` 產生最終回覆內容後，也會將 AI 端資料送入 `Persistence Layer`
- `Persistence Layer` 在最後分別承接使用者端與 AI 端的對話紀錄，並保存至資料庫

這樣每一輪對話都會留下最小可用的紀錄基礎，避免之後只有部分內容被保存。

### 3. 歷史資料由 `Persistence Layer` 整理後回傳

對話紀錄保存不只包含存入，也包含後續查詢與回傳。

目前設計上，歷史查詢流程的責任切法是：

- 前端向後端請求指定對話的歷史資料
- 控制層承接查詢請求
- 控制層將查詢需求送入 `Persistence Layer`
- `Persistence Layer` 自持久化資料中取出對應內容
- `Persistence Layer` 整理並打包為前端可讀的歷史對話 JSON
- 控制層再將該結果回傳給前端

這樣可讓前端在刷新或重新進入頁面時，根據歷史資料重建對話畫面。

---

## 最小保存範圍

在 MVP2 階段，對話紀錄保存先維持最小範圍，只要求能支撐：

- 建立新對話
- 保存每輪對話中的使用者輸入與 AI 回覆
- 查詢指定對話的歷史資料
- 回傳前端可重新整理畫面的歷史資料格式

現階段先不處理：

- 更細的訊息分類
- 複雜回滾機制
- 多版本對話分支
- 規劃結果的額外持久化策略

---

## 與正式規格的關係

本設計文件對應的正式規格主要包括：

- `docs/specs/api_spec/conversation_create_api.md`
  - 前端初始化時向後端建立新對話的功能。

- `docs/specs/api_spec/raw_request_api.md`
  - 前端每次送出對話內容至後端的功能。

- `docs/specs/api_spec/conversation_history_api.md`
  - 前端向後端請求既有對話歷史資料的功能。

- `docs/specs/data_contract/persistence_conversation_record_store_contract.md`
  - 控制層或模組將對話紀錄資料送入 `Persistence Layer` 時的存入資料交換。

- `docs/specs/data_contract/persistence_conversation_record_history_contract.md`
  - `Persistence Layer` 將歷史對話資料整理後回傳給後端控制層時的資料交換。

- `docs/specs/data_contract/flow_stage_reference.md`
  - 對話紀錄保存相關流程在整體主流程中的節點位置與前後關係。

- `docs/specs/database/conversation_record_entities.md`
  - `Persistence Layer` 在資料庫中所承接的資料表結構。

若後續實作需要落成程式中的正式資料模型、流程控制與持久化行為，應優先以上述規格文件為準；本文件則保留設計脈絡與收斂理由，供後續回顧與調整參考。
