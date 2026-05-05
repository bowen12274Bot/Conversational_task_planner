from typing import Any

from pydantic import BaseModel, Field


class PromptBuilderOutput(BaseModel):
    """由 AI service layer 的 prompt builder 產生的提示建構輸出資料，用於承接提示內容與對應 Provider payload。"""

    # 提供模型閱讀的提示文字內容
    prompt_text: str = Field(..., min_length=1)
    # 依 Provider 格式要求組裝完成的 request payload
    request_payload: dict[str, Any] = Field(default_factory=dict)


class ProviderExecutionConfig(BaseModel):
    """由 AI service layer 在單次 Provider 呼叫前整理出的執行設定資料。"""

    # 本次呼叫所使用的 Provider 識別
    provider_id: str = Field(..., min_length=1)
    # Provider API 的基礎網址
    base_url: str = Field(..., min_length=1)
    # 單次呼叫可等待的最大秒數
    timeout_seconds: float = Field(..., gt=0)
    # 對應 Provider 的私有 API 金鑰；缺值時仍可保留物件，交由後續流程回傳結構化錯誤
    api_key: str | None = None


class ProviderRequestData(BaseModel):
    """由 AI service layer 整理後交付給 provider client 的單次呼叫資料。"""

    # 本次選定的模型設定資料
    selected_model_config: dict[str, Any] = Field(default_factory=dict)
    # 已完成組裝的 Provider request payload
    request_payload: dict[str, Any] = Field(default_factory=dict)
    # 本次呼叫所需的 Provider 執行設定
    execution_config: ProviderExecutionConfig
