import json
from typing import Any

from app.schemas import ModuleToAIRequest


def render_prompt_text(request: ModuleToAIRequest) -> str:
    """將模組提供的結構化 AI 任務資料轉為最終純文字 prompt。"""

    input_data = request.input_data
    if _is_sectioned_prompt_input(input_data):
        return _render_sectioned_prompt(
            task_type=request.task_type,
            group_name=request.group_name,
            capability_level=request.capability_level,
            input_data=input_data,
            format_requirements=request.format_requirements,
        )

    payload = {
        "task_type": request.task_type,
        "group_name": request.group_name,
        "capability_level": request.capability_level,
        "input_data": input_data,
        "format_requirements": request.format_requirements,
    }
    return json.dumps(payload, ensure_ascii=False)


def _is_sectioned_prompt_input(input_data: dict[str, Any]) -> bool:
    """判斷 input_data 是否已符合分段 prompt 的結構。"""

    required_keys = {
        "rules",
        "task",
        "context",
        "examples",
        "output_target",
    }
    return required_keys.issubset(input_data.keys())


def _render_sectioned_prompt(
    task_type: str,
    group_name: str,
    capability_level: str,
    input_data: dict[str, Any],
    format_requirements: dict[str, Any] | None,
) -> str:
    """將分段式 input_data 組成最終 prompt 文字。"""

    # 分段 prompt 目前會依固定順序翻成文字：
    
    # [rules]
    # ...
    
    # [task]
    # ...
    
    # [context]
    # {
    #   ...
    # }
    
    # [examples]
    # [
    #   ...
    # ]
    
    # [output_target]
    # ...
    
    # [format_requirements]
    # {
    #   ...
    # }
    
    # 其中 task_type / group_name / capability_level 屬於系統層 metadata，
    # 目前不直接 render 給模型；renderer 只處理實際 prompt 內容。
    
    # 也就是模組層先提供 section 化資料，renderer 再把每段標上標題，
    # 文字內容維持原樣，dict / list 則轉為 JSON pretty-print。
    sections = [
        _render_text_section("rules", input_data["rules"]),
        _render_text_section("task", input_data["task"]),
        _render_text_section("context", input_data["context"]),
        _render_text_section("examples", input_data["examples"]),
        _render_text_section("output_target", input_data["output_target"]),
    ]

    if format_requirements is not None:
        sections.append(
            _render_text_section("format_requirements", format_requirements)
        )

    return "\n\n".join(sections)


def _render_text_section(title: str, content: Any) -> str:
    """將單一 section 組成可讀的 prompt 段落。"""

    return f"[{title}]\n{_stringify_content(content)}"


def _stringify_content(content: Any) -> str:
    """將 section 內容整理為可讀的文字。"""

    if isinstance(content, str):
        return content

    return json.dumps(content, ensure_ascii=False, indent=2)
