# 專案入口

- [frontend](./frontend)
  - 前端專案入口；啟動指令：`npm run dev:frontend`

- [backend](./backend)
  - 後端專案入口；啟動指令：`npm run dev:backend`，資料庫初始化：`npm run init:backend`

- [data](./data)
  - 本機資料入口；目前主要存放 SQLite 資料庫檔案 `app.db`，資料庫的資料不共用，各自做本地存取

- [tests](./tests)
  - 測試入口；目前包含後端 smoke tests，執行指令：`npm run test:backend`

- [docs/README.md](./docs/README.md)
  - 專案文件入口，包含專案總覽、模組說明、系統設計與架構文件

- [docs/quick_start.md](./docs/quick_start.md)
  - 專案環境快速啟動說明，包含前後端啟動與資料庫初始化指令

- [word](./word)
  - 學校提供的相關資料、樣板，以及需要繳交的內容

- [CONTRIBUTING.md](./CONTRIBUTING.md)
  - 專案協作與貢獻指南
