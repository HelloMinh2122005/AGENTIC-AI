#!/usr/bin/env python3
"""Demo 0: send one issue to an LLM and print its free-form triage using Google Gemini."""

from __future__ import annotations

import argparse

from demo_common import gemini_client, model_name
from google.genai import types

DEFAULT_ISSUE = "Nút thanh toán trả HTTP 500 với mọi thẻ Visa từ 14:30."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue", default=DEFAULT_ISSUE, help="Nội dung issue cần phân loại.")
    args = parser.parse_args()

    client = gemini_client()
    response = client.models.generate_content(
        model=model_name(),
        contents=args.issue,
        config=types.GenerateContentConfig(
            system_instruction="Bạn hỗ trợ phân loại issue phần mềm.",
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    print(response.text)


if __name__ == "__main__":
    main()
