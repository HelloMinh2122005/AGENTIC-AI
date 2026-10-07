#!/usr/bin/env python3
"""Demo 05: Chatbot multi-turn tối giản để thấy cơ chế của một LLM-Powered App (Google Gemini API).

Chạy:  python 05_chatbot_multiturn.py   (mở http://127.0.0.1:8000)

Backend là một HTTP server stdlib. Mỗi lượt chat, trình duyệt gửi TOÀN BỘ
lịch sử hội thoại lên server; server ghép thêm system prompt rồi gọi Gemini API.
Server trả về câu trả lời, ĐÚNG payload messages đã gửi đi, và usage do Gemini
trả về. Pane bên phải hiển thị payload đó để sinh viên thấy:
LLM không có "trí nhớ" — mỗi lượt ta phải gửi lại cả ngữ cảnh.
"""

from __future__ import annotations

import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from demo_common import gemini_client, model_name
from google.genai import types

# Bind mọi interface để máy khác trong LAN truy cập được (đổi qua env nếu cần).
HOST = os.getenv("CHATBOT_HOST", "0.0.0.0")
PORT = int(os.getenv("CHATBOT_PORT", "8000"))

DEFAULT_SYSTEM = "Bạn là trợ lý AI thân thiện, trả lời ngắn gọn bằng tiếng Việt."

# Giao diện tách riêng ra file .html cạnh script này; Python chỉ serve nó.
PAGE_PATH = Path(__file__).resolve().parent / "05_chatbot_multiturn.html"


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        page = PAGE_PATH.read_text(encoding="utf-8")
        body = page.replace("__DEFAULT_SYSTEM__", DEFAULT_SYSTEM).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/chat":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        system = (payload.get("system") or DEFAULT_SYSTEM).strip()
        turns = payload.get("messages", [])

        # Ghép prompt gửi đi để hiển thị trên UI bên phải
        request_messages = [{"role": "system", "content": system}]
        for turn in turns:
            request_messages.append(
                {"role": turn["role"], "content": turn["content"]}
            )

        # Chuyển đổi sang format Content của Google Gemini API
        contents = []
        for turn in turns:
            role = "user" if turn.get("role") == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=turn.get("content", ""))],
                )
            )

        try:
            client = gemini_client()
            model = model_name()
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except Exception as exc:  # surface provider/config errors in the UI
            self._send_json({"error": f"{type(exc).__name__}: {exc}"}, status=200)
            return

        reply = response.text or ""
        usage = None
        if getattr(response, "usage_metadata", None) is not None:
            meta = response.usage_metadata
            usage = {
                "prompt_tokens": getattr(meta, "prompt_token_count", 0),
                "completion_tokens": getattr(meta, "candidates_token_count", 0),
                "total_tokens": getattr(meta, "total_token_count", 0),
            }
            cached = getattr(meta, "cached_content_token_count", None)
            if cached is not None and cached > 0:
                usage["cached_tokens"] = cached

        self._send_json(
            {"reply": reply, "request": request_messages, "usage": usage}
        )

    def log_message(self, *args) -> None:  # keep the console quiet
        pass


def _lan_ip() -> str:
    """Best-effort địa chỉ IP LAN của máy (không thực sự gửi gói tin)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return ""
    finally:
        sock.close()


def main() -> None:
    # Validate configuration up front so misconfig fails before the server starts.
    if not PAGE_PATH.exists():
        raise RuntimeError(f"Không tìm thấy giao diện: {PAGE_PATH}")
    model = model_name()
    gemini_client()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    lan_ip = _lan_ip()
    print(f"Chatbot demo (Gemini: {model}) đang chạy (Ctrl+C để dừng):")
    print(f"  • Máy này : http://127.0.0.1:{PORT}")
    if lan_ip:
        print(f"  • Qua LAN : http://{lan_ip}:{PORT}   (máy khác cùng mạng mở link này)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng.")
        server.shutdown()


if __name__ == "__main__":
    main()
