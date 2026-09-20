"""
Lightweight smoke test: instantiates the REAL xiaozhi-server LLM provider
class (core/providers/llm/openai/openai.py) with the config we generated
from .env.local, and streams a response from OpenRouter.

This validates the exact code path the ESP32 backend will use, without
needing to install the full ML stack (torch/funasr/sherpa_onnx/etc).

Usage (from Ameo/):
    server-backend/main/xiaozhi-server/.venv_test/Scripts/python \
        scripts/test_openrouter_llm_provider.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = ROOT / "server-backend" / "main" / "xiaozhi-server"
sys.path.insert(0, str(SERVER_DIR))

import yaml  # noqa: E402

CONFIG_FILE = SERVER_DIR / "data" / ".config.yaml"

if not CONFIG_FILE.exists():
    print("ERROR: run `python scripts/apply_openrouter_config.py` first.")
    sys.exit(1)

cfg = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
llm_cfg = cfg["LLM"]["OpenRouterLLM"]

import types  # noqa: E402

# Stub out core.utils.util — it pulls in opuslib_next (needs native libopus,
# irrelevant for this text-only LLM smoke test) just to expose check_model_key.
_fake_util = types.ModuleType("core.utils.util")
_fake_util.check_model_key = lambda *a, **k: None
sys.modules["core.utils.util"] = _fake_util

from core.providers.llm.openai.openai import LLMProvider  # noqa: E402

provider = LLMProvider(llm_cfg)

dialogue = [
    {"role": "system", "content": "You are Ameo, a helpful voice assistant running on an ESP32."},
    {"role": "user", "content": "In one short sentence, confirm you're alive and say your name."},
]

print(f"Model: {llm_cfg['model_name']}  |  Base URL: {llm_cfg['base_url']}")
print("Response: ", end="", flush=True)
for chunk in provider.response("test-session", dialogue):
    print(chunk, end="", flush=True)
print()
