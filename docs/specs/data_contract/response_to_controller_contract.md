# Response 輸出資料契約

本文件用於定義 `Response Module` 對外輸出的統一資料物件。

此資料物件不綁定單一上游業務來源。雖然目前實作主要由 `Questioning Module` 的追問情境驅動，但後續若新增規劃摘要、修改說明或狀態回覆等業務，仍應優先以同一份輸出契約收斂 `Response Module` 的對外結果。

---

## 資料物件：Response 輸出資料

### 定義

由 `Response Module` 生成的、適合交回控制層並提供前端顯示的最終回覆內容。

### 組成內容

- 回覆文字
- 回覆類型

### 作用

- 作為 `Response Module` 對控制層的統一輸出物件
- 提供前端顯示給使用者的自然語言回覆
- 將不同上游業務結果轉換為一致的回覆輸出格式

### 特性

- `ResponseOutput` 的責任是表達 `Response Module` 的對外結果，而不是上游模組的中介資料
- 回覆內容可隨上游業務而有不同類型
- 現階段 schema 先維持最小範圍，只保留目前明確穩定的共通欄位

---

## 欄位定義

### `reply_text`

- 型別：`string`
- 說明：適合直接顯示給使用者的自然語言回覆文字

### `response_type`

- 型別：固定值集合
- 說明：標示本次回覆在互動流程中的角色

現階段僅明確定義以下值：

- `follow_up_question`
  - 表示目前資訊不足，`Response Module` 產出的回覆內容是為了引導使用者補充後續規劃所需資訊。

---

## 與其他資料契約的關係

- `QuestioningDecision` 屬於 `Questioning Module` 的輸出，定義於 [input_to_questioning_contract.md](./input_to_questioning_contract.md)
- `ResponseOutput` 屬於 `Response Module` 的對外輸出，因此獨立定義於本文件
- 後續若 `Response Module` 新增其他業務入口，應優先評估是否仍可共用本文件定義的統一輸出格式
