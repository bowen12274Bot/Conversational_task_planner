# 設計構想說明

更新日期時間：2026-04-20 14:15:00

本資料夾用於整理專案中的設計與想法相關文件。

此處的文件可能包含尚未實作的設計方向，也可能包含過去設計想法的整理與保留，作為後續討論、回顧與形成正式規格時的參考。

## 文件定位

- 記錄設計想法、方向與階段性構想
- 保留尚未定案但值得追蹤的方案
- 保留過去設計想法與收斂過程的紀錄
- 協助從設計內容逐步收斂為正式規格

## 與 `specs/` 的區別

- `design/`
  - 放設計構想、方案討論、想法紀錄與收斂文件

- `specs/`
  - 放已整理為正式規格、可供實作直接引用的文件

## 文件要求

- `design/` 資料夾中的文件應標示更新日期時間
- 更新時間用於表示該設計內容是否仍具參考價值

## 目前主要文件

- [ai_role_design.md](./ai_role_design.md)
  - 整理 AI 在系統中的角色定位與使用邊界
- [flow_control_design.md](./flow_control_design.md)
  - 整理後端流程控制層與 `flow_stage` 設計構想
- [planning_module_create_design.md](./planning_module_create_design.md)
  - 整理建立規劃路線的 Planning Module 設計
- [planning_module_revise_design.md](./planning_module_revise_design.md)
  - 整理修改規劃路線的 Planning Module 設計
- [questioning_module_design.md](./questioning_module_design.md)
  - 整理追問模組的責任與設計方向
- [chat_module_design.md](./chat_module_design.md)
  - 整理 Chat Module 的定位、責任邊界與控制層路線
