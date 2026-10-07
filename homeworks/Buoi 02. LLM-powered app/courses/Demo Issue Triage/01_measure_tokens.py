#!/usr/bin/env python3
"""Demo 01: Compare English and Vietnamese token counts using Google Gemini API."""

from __future__ import annotations

from demo_common import gemini_client, model_name

ENGLISH = (
    "The Aqueduct of Segovia is a Roman aqueduct in Segovia, Spain. "
    "It was built around the first century AD to channel water from "
    "springs in the mountains seventeen kilometres away."
)
VIETNAMESE = (
    "Cầu máng Segovia là một cầu máng dẫn nước của người La Mã tại "
    "Segovia, Tây Ban Nha. Công trình được xây dựng vào khoảng thế kỷ "
    "thứ nhất sau Công nguyên để dẫn nước từ các con suối trên núi "
    "cách đó mười bảy ki-lô-mét."
)


def main() -> None:
    client = gemini_client()
    model = model_name()

    print(f"=== ĐO LƯỜNG TOKEN VỚI GEMINI API (Model: {model}) ===")
    en_res = client.models.count_tokens(model=model, contents=ENGLISH)
    vi_res = client.models.count_tokens(model=model, contents=VIETNAMESE)

    en_tokens = en_res.total_tokens
    vi_tokens = vi_res.total_tokens
    ratio = vi_tokens / en_tokens if en_tokens else 0.0

    print(f"Gemini Tokenizer ({model}): EN={en_tokens} VI={vi_tokens} ratio={ratio:.2f}")

    # So sánh với tiktoken (nếu có cài đặt)
    try:
        import tiktoken
        print("\n=== SO SÁNH VỚI TIKTOKEN ===")
        for name in ("cl100k_base", "o200k_base"):
            encoding = tiktoken.get_encoding(name)
            english_tokens = len(encoding.encode(ENGLISH))
            vietnamese_tokens = len(encoding.encode(VIETNAMESE))
            print(
                f"{name}: EN={english_tokens} VI={vietnamese_tokens} "
                f"ratio={vietnamese_tokens / english_tokens:.2f}"
            )
    except ImportError:
        pass


if __name__ == "__main__":
    main()
