from app.schemas import ChatModuleInput, PlanningIntent
from app.services.modules.chat.prompt import build_chat_prompt_spec


def test_build_chat_prompt_spec_allows_multiple_answer_types() -> None:
    prompt_spec = build_chat_prompt_spec(
        ChatModuleInput(
            raw_requirement="第三階段有沒有練習方向和學習管道？",
            requirement_context="使用者詢問第三階段的練習方向與學習管道。",
            planning_intent=PlanningIntent(
                intent_type="chat",
                target_main_task_order=3,
                confidence="high",
            ),
            existing_plan_outline=[
                {"order": 3, "title": "第三階段：實戰衝刺期"}
            ],
        )
    )

    format_requirements = prompt_spec["format_requirements"]
    example_output = prompt_spec["input_data"]["examples"][0]["output"]

    assert "answer_types" in format_requirements["required_fields"]
    assert example_output["answer_types"] == [
        "execution_advice",
        "resource_suggestion",
    ]
    assert "Do not claim that an action was performed" in prompt_spec["input_data"]["task"]
