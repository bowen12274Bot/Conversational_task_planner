# 快速啟動

本文件整理目前專案環境架構的快速啟動方式，包含前端、後端的套件安裝、資料庫初始化與啟動指令。

## 開始前確認

- Node.js 已安裝
- Python 已安裝

## 初次啟動順序

1. 安裝前端套件 `npm run install:frontend`
2. 安裝後端套件 `npm run install:backend`
3. 初始化資料庫 `npm run init:backend`
4. 啟動後端 `npm run dev:backend`
5. 啟動前端 `npm run dev:frontend`
   
## 第一次建置環境

開啟powershell終端機，在專案根目錄執行：

```powershell
npm run install:frontend
npm run install:backend
```
第一個是下載本地的前端依賴套件
第二個是下載本地的後端依賴套件

## 前端啟動

開啟powershell終端機，在專案根目錄執行：

```powershell
npm run dev:frontend
```

預設會啟動 Vite 開發伺服器，常見網址為：

```text
http://localhost:5173/
```
在遊覽器貼上網址並進入，隨後就會開啟前端網頁。

## 後端啟動

同時開啟powershell終端機，在專案根目錄執行：

```powershell
npm run dev:backend
```

預設會啟動 FastAPI 開發伺服器，常見網址為：

```text
http://127.0.0.1:8000/
```
須維持後端伺服器長時間啟動。

## 初始模組載入與資料庫建表

若要先初始化 SQLite 資料庫與建表，請開啟powershell終端機，在專案根目錄執行：

```powershell
npm run init:backend
```

目前此指令會建立資料庫檔案，並依照 SQLAlchemy `Base.metadata` 進行建表。

## 測試 API

後端啟動後，可直接開啟下列網址確認 API 狀態：

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/ping`
- `http://127.0.0.1:8000/api/db-check`

若前後端都已啟動，前端首頁會呼叫 `/api/ping` 並顯示連線結果。
