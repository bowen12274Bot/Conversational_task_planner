# 資料契約說明

本資料夾用於整理系統中的資料契約規範，聚焦於模組之間傳遞的資料定義、資料物件邊界與資料內容約定。

## 文件定位

本資料夾中的文件主要用於描述系統在不同流程階段中，模組之間交換的資料內容與資料關係。這些文件的重點不在於資料庫表設計，而在於資料物件本身的語意、用途與邊界。

目前規劃會以各流程區段的資料契約文件為主，逐步整理模組之間交換的資料內容。

## 文件說明

- 後續可依流程主題新增個別契約文件
  - 例如 `input_to_questioning_contract.md`
  - 或 `questioning_to_planning_contract.md`

## 命名規範

本資料夾中的文件命名需反映文件用途，避免使用臨時性、模糊或任意命名。不同類型的文件，應採用不同的命名方式。

### 一、概念與總覽文件

用於描述跨流程共用的概念資料物件、整體關係或總體原則。

命名方式如下：
- 採用固定語意名稱
- 使用小寫英文字母與底線
- 名稱應直接對應文件角色

可採用的名稱例如：
- `conceptual_models.md`
- `relationship_principles.md`
- `naming_conventions.md`

若文件僅作為設計過程中的暫存思考或內部筆記，應移至 `.private/notes/`，不納入本資料夾。

### 二、流程型資料契約文件

用於描述某一段流程中，模組之間傳遞的資料契約。

命名方式如下：
- 採用 `{from}_to_{to}_contract.md`
- `from` 與 `to` 表示資料流的起點與終點
- 名稱描述的是資料傳遞區段，不是單一模組名稱

可採用的名稱例如：
- `input_to_questioning_contract.md`
- `questioning_to_planning_contract.md`
- `planning_to_response_contract.md`

### 三、資料關係定義文件

用於描述某一組資料物件之間的關係、依附性、包含關係與責任邊界。

命名方式如下：
- 採用 `{domain}_relationships.md`
- `domain` 表示該文件聚焦的資料範圍

可採用的名稱例如：
- `questioning_relationships.md`
- `planning_relationships.md`
- `context_relationships.md`

## 命名限制

- 不使用 `temp`、`draft2`、`new`、`test` 這類臨時名稱
- 不使用過短且無法判斷用途的名稱
- 不以實作技術命名概念文件，例如 `schema1.md`
- 若文件描述的是流程契約，優先使用 `*_contract.md`
- 若文件描述的是資料關係，優先使用 `*_relationships.md`
