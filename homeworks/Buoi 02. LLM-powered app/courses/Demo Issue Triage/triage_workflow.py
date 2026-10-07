"""Application-controlled Issue Triage workflow shared by CLI and Streamlit demos using Google Gemini API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

COMPONENT_OWNERS = {
    "payment": "checkout-platform",
    "identity": "identity-platform",
    "search": "search-platform",
}

COMPONENT_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_component_owner",
            description=(
                "Trả team chịu trách nhiệm cho một software component. "
                "Chỉ dùng component trong danh sách: payment, identity, search."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "component": types.Schema(
                        type="STRING",
                        enum=list(COMPONENT_OWNERS),
                        description="Tên component (payment, identity, search)",
                    )
                },
                required=["component"],
            ),
        )
    ]
)

SYSTEM_PROMPT = (
    "Bạn hỗ trợ triage issue phần mềm. Khi cần biết team xử lý một component, "
    "hãy gọi get_component_owner. Component hợp lệ là payment, identity hoặc "
    "search. Không tự thực thi tool."
)


@dataclass(frozen=True)
class ToolTrace:
    """One validated tool request and the application result returned to the model."""

    call_id: str
    name: str
    arguments: dict[str, Any]
    result: dict[str, str]


@dataclass(frozen=True)
class TriageResult:
    """Consumer-facing result of a complete, single-round Issue Triage run."""

    tool_traces: tuple[ToolTrace, ...]
    final_response: str


def get_component_owner(component: str) -> str:
    """Return the owner only for application-approved components."""
    return COMPONENT_OWNERS[component]


def execute_tool_call(name: str, raw_arguments: str | dict[str, Any]) -> dict[str, str]:
    """Validate a requested tool and its semantics before application execution."""
    if name != "get_component_owner":
        raise ValueError(f"Tool is not allowed: {name}")

    if isinstance(raw_arguments, str):
        arguments = json.loads(raw_arguments)
    else:
        arguments = raw_arguments

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")
    if set(arguments) != {"component"} or not isinstance(arguments["component"], str):
        raise ValueError("Tool arguments must contain exactly one string: component.")

    component = arguments["component"]
    if component not in COMPONENT_OWNERS:
        raise ValueError(f"Unknown component: {component}")

    return {"component": component, "owner": get_component_owner(component)}


def triage_issue(client: genai.Client, model: str, issue: str) -> TriageResult:
    """Triage one issue, execute validated owner lookups, and return the final answer."""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=issue)],
        )
    ]

    first_response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[COMPONENT_TOOL],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    tool_calls = first_response.function_calls or []
    if not tool_calls:
        return TriageResult(
            tool_traces=(),
            final_response=first_response.text or "(Model returned no text.)",
        )

    contents.append(first_response.candidates[0].content)
    traces: list[ToolTrace] = []

    for idx, tool_call in enumerate(tool_calls, start=1):
        args = dict(tool_call.args) if tool_call.args else {}
        result = execute_tool_call(tool_call.name, args)
        call_id = getattr(tool_call, "id", None) or f"call_{idx}"
        traces.append(
            ToolTrace(
                call_id=call_id,
                name=tool_call.name,
                arguments=args,
                result=result,
            )
        )
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=tool_call.name,
                        response=result,
                    )
                ],
            )
        )

    final_response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[COMPONENT_TOOL],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    return TriageResult(
        tool_traces=tuple(traces),
        final_response=final_response.text or "(Model returned no text.)",
    )
