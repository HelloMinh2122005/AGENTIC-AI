"""Shared configuration for the Buổi 02 executable demos using Google Gemini API."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import models

# Vô hiệu hóa cảnh báo AFC mặc định của google-genai vì các demo của Buổi 02
# chủ động tự quản lý luồng Application-Controlled Function Calling & Tool Trace
models.Models._logged_afc_warning = True
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

SCRIPT_DIRECTORY = Path(__file__).resolve().parent


def load_environment() -> None:
    """Load optional repository- and demo-local .env files without overriding OS env."""
    search_dirs = [
        SCRIPT_DIRECTORY,
        SCRIPT_DIRECTORY.parent,
        SCRIPT_DIRECTORY.parents[1],
        SCRIPT_DIRECTORY.parents[2] if len(SCRIPT_DIRECTORY.parents) > 2 else SCRIPT_DIRECTORY,
    ]
    for directory in search_dirs:
        env_file = directory / ".env"
        if env_file.is_file():
            load_dotenv(env_file)


def model_name() -> str:
    load_environment()
    return os.getenv("GEMINI_MODEL") or os.getenv("OPENAI_MODEL") or "gemini-3.5-flash-lite"


def gemini_client() -> genai.Client:
    """Create a client for the Google Gemini API."""
    load_environment()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required. Copy .env.example to .env and set your Gemini API key."
        )
    return genai.Client(api_key=api_key)


# Compatibility alias
openai_client = gemini_client
