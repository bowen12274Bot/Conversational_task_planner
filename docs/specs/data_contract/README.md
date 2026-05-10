# 資料契約說明

更新日期時間：2026-05-11 00:44:00

本資料夾用於整理系統中的資料契約文件，重點在於描述架構層與模組層之間交換的資料內容。

---

## 文件分層

目前文件可分為以下三類：

- 架構層資料契約
  - [frontend_to_controller_contract.md](./frontend_to_controller_contract.md)
  - [controller_flow_transfer_contract.md](./controller_flow_transfer_contract.md)
  - [controller_to_text_output_contract.md](./controller_to_text_output_contract.md)

- 模組層資料契約
  - [input_to_questioning_contract.md](./input_to_questioning_contract.md)
  - [response_to_controller_contract.md](./response_to_controller_contract.md)
  - [module_to_ai_contract.md](./module_to_ai_contract.md)

- 持久化相關資料契約
  - [conversation_contract.md](./conversation_contract.md)

- 共用參考文件
  - [flow_stage_reference.md](./flow_stage_reference.md)

---

## 命名規則

- 流程型資料契約文件採用 `{from}_to_{to}_contract.md`
- 共用參考文件採用能直接表達用途的名稱
