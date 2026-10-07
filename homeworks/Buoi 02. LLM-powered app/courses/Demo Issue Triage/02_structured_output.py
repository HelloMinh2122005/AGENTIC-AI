#!/usr/bin/env python3
"""Demo 02: Contrast prompt-only JSON with provider-constrained structured output using Google Gemini."""

from __future__ import annotations

import argparse
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from demo_common import gemini_client, model_name
from google.genai import types

DEFAULT_ISSUE = "Nút thanh toán trả HTTP 500 với mọi thẻ Visa từ 14:30."


class IssueTriage(BaseModel):
    """The machine-readable contract between this demo and the model."""

    status: Literal["classified", "insufficient_data", "out_of_scope"]
    severity: Literal["P0", "P1", "P2", "P3"] | None = None
    component: str | None = None
    needs_urgent_response: bool = False
    reason: str = Field(description="Lý do ngắn gọn dựa trên dữ liệu issue")


SYSTEM_PROMPT = """Bạn là kỹ sư phụ trách phân loại sự cố phần mềm.
Phân loại severity theo P0/P1/P2/P3 dựa trên dữ liệu issue. Nếu dữ liệu không
đủ để phân loại, dùng status=insufficient_data thay vì đoán. Chỉ dùng
status=out_of_scope khi nội dung không phải issue phần mềm."""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue", default=DEFAULT_ISSUE, help="Nội dung issue cần phân loại.")
    args = parser.parse_args()

    client = gemini_client()
    model = model_name()

    # 1. Prompt-only: chỉ yêu cầu JSON qua câu lệnh (không ép schema từ API)
    prompt_only = client.models.generate_content(
        model=model,
        contents=f"{args.issue}\n\nChỉ trả về một JSON object đúng schema.",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    print("=== Prompt-only response ===")
    print(prompt_only.text)

    # 2. Constrained: ép buộc cấu trúc qua response_schema (Pydantic model) của Gemini API
    constrained = client.models.generate_content(
        model=model,
        contents=args.issue,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=IssueTriage,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    parsed = constrained.parsed
    if parsed is None and constrained.text:
        parsed = IssueTriage.model_validate_json(constrained.text)

    if parsed is None:
        raise RuntimeError("Model did not return a structured IssueTriage response.")

    print("\n=== Constrained structured response (Pydantic validated) ===")
    print(parsed.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
