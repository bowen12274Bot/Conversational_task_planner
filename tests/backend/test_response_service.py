from app.schemas import AIToModuleResult
from app.services.modules.response import service as response_service


def test_extract_response_text_keeps_only_final_follow_up_reply() -> None:
    ai_result = AIToModuleResult(
        success=True,
        output_result={
            "text": (
                "Helpful planning assistant.\n"
                "Natural Traditional Chinese (Taiwan).\n"
                "* Draft 1: 為了幫你規劃得更準確，我想先確認目前進度。\n"
                "Final Polish:\n"
                "為了幫你做出更準確的規劃，我想先確認兩件事：目前作業進行到哪裡了？難度大約是什麼程度呢？"
            ),
            "provider": "mock",
            "model_name": "mock-model",
        },
    )

    reply_text = response_service._extract_response_text(ai_result)

    assert (
        reply_text
        == "為了幫你做出更準確的規劃，我想先確認兩件事：目前作業進行到哪裡了？難度大約是什麼程度呢？"
    )


def test_extract_response_text_unwraps_final_quoted_reply() -> None:
    ai_result = AIToModuleResult(
        success=True,
        output_result={
            "text": (
                "* Constraint check\n"
                "\"為了幫你安排得更準確，我想先確認兩件事：這份作業預計什麼時候完成？目前進度如何？\""
            ),
            "provider": "mock",
            "model_name": "mock-model",
        },
    )

    reply_text = response_service._extract_response_text(ai_result)

    assert (
        reply_text
        == "為了幫你安排得更準確，我想先確認兩件事：這份作業預計什麼時候完成？目前進度如何？"
    )
