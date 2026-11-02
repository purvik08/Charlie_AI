"""
Colibri Adapter for Charlie AI.

Integrates the Colibri local LLM engine (colibri-main/) which exposes
an OpenAI-compatible REST server at http://127.0.0.1:8000/v1.

Colibri runs very large mixture-of-experts models (e.g., GLM-5.2 744B,
DeepSeek V4, Qwen3.6, OLMoE) by streaming expert weights from disk,
so only ~10–11 GB of RAM is needed even for enormous models.

Charlie integrates Colibri as an *optional* alternative LLM backend.
When Colibri's server is running it is discovered automatically; when
it is not running the adapter gracefully falls back to Ollama / the
configured primary LLM.

Key capabilities surfaced here:
- Listing installed Colibri models
- Checking server status
- Sending completions through the OpenAI-compatible API
- Launching / stopping the Colibri server (Windows: coli.cmd)
"""

import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_COLIBRI_ROOT = _PROJECT_ROOT / "colibri-main"
_COLI_CMD = _COLIBRI_ROOT / "c" / "coli.cmd"       # Windows batch wrapper
_COLI_SCRIPT = _COLIBRI_ROOT / "c" / "coli"         # POSIX / direct script

# Default Colibri server address (OpenAI-compatible)
COLIBRI_BASE_URL = "http://127.0.0.1:8000/v1"
COLIBRI_CHAT_URL = f"{COLIBRI_BASE_URL}/chat/completions"
COLIBRI_MODELS_URL = f"{COLIBRI_BASE_URL}/models"
COLIBRI_HEALTH_URL = "http://127.0.0.1:8000/"


class ColibriAdapter:
    """
    Adapter that connects Charlie AI to a running Colibri LLM server.

    Usage example:
        adapter = ColibriAdapter()
        if adapter.is_server_running():
            response = adapter.chat("Tell me about black holes.")
            print(response)
        else:
            print(adapter.start_guide())
    """

    def __init__(
        self,
        base_url: str = COLIBRI_BASE_URL,
        timeout: int = 60,
        model: Optional[str] = None,
    ):
        """
        Args:
            base_url: Base URL of the Colibri OpenAI-compatible API.
            timeout: HTTP request timeout in seconds.
            model: Force a specific model name.  When None the first available
                   model returned by the server is used.
        """
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/chat/completions"
        self.models_url = f"{self.base_url}/models"
        self.health_url = "http://127.0.0.1:8000/"
        self.timeout = timeout
        self._forced_model = model
        self._cached_models: Optional[List[str]] = None

    # ------------------------------------------------------------------ status
    def is_server_running(self) -> bool:
        """Return True when the Colibri server is reachable."""
        try:
            resp = requests.get(self.health_url, timeout=3)
            return resp.status_code < 500
        except requests.RequestException:
            return False

    def get_models(self, refresh: bool = False) -> List[str]:
        """
        Return a list of model IDs available from the Colibri server.

        Returns an empty list when the server is not running.
        """
        if self._cached_models is not None and not refresh:
            return self._cached_models
        try:
            resp = requests.get(self.models_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = [m["id"] for m in data.get("data", [])]
                self._cached_models = models
                return models
        except requests.RequestException:
            pass
        return []

    def active_model(self) -> Optional[str]:
        """Return the model that will be used for inference."""
        if self._forced_model:
            return self._forced_model
        models = self.get_models()
        return models[0] if models else None

    # ------------------------------------------------------------------ inference
    def chat(
        self,
        message: str,
        system_prompt: str = "You are Charlie, a helpful AI assistant.",
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Send a chat message to the Colibri server and return the reply.

        Args:
            message: The user's message.
            system_prompt: System-level instruction.
            history: Optional list of prior messages [{"role": ..., "content": ...}].
            max_tokens: Maximum tokens in the reply.
            temperature: Sampling temperature.

        Returns:
            The assistant's reply as a string, or an error/guidance message.
        """
        if not self.is_server_running():
            return (
                "Colibri LLM server is not running.\n"
                + self.start_guide()
            )

        model = self.active_model()
        if not model:
            return "No model loaded in Colibri. Run 'coli chat' or 'coli web' first."

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        try:
            resp = requests.post(self.chat_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
            return "Empty response from Colibri."
        except requests.Timeout:
            return "Colibri request timed out. The model may still be loading."
        except requests.RequestException as exc:
            return f"Colibri request failed: {exc}"

    def chat_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Low-level chat endpoint accepting a full messages list.
        Compatible with the ModelManager.chat() interface.
        """
        if not self.is_server_running():
            return ""

        model = self.active_model()
        if not model:
            return ""

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        try:
            resp = requests.post(self.chat_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
        except requests.RequestException as exc:
            logger.warning("ColibriAdapter chat_messages failed: %s", exc)
        return ""

    # ------------------------------------------------------------------ server management
    def start_server(self, wait_seconds: int = 30) -> str:
        """
        Attempt to start the Colibri server in the background.

        Works on Windows (via coli.cmd) and Unix (via the coli script).
        If no installed coli executable is found, returns a setup guide.
        """
        if self.is_server_running():
            model = self.active_model()
            return f"Colibri server is already running (model: {model or 'loading…'})."

        coli = self._find_coli()
        if not coli:
            return self.start_guide()

        try:
            if os.name == "nt":
                subprocess.Popen(
                    [str(coli), "serve"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    cwd=str(_COLIBRI_ROOT),
                )
            else:
                subprocess.Popen(
                    [str(coli), "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=str(_COLIBRI_ROOT),
                )
        except Exception as exc:
            return f"Failed to launch Colibri: {exc}\n\n{self.start_guide()}"

        # Poll until ready
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            if self.is_server_running():
                model = self.active_model()
                return f"Colibri server started (model: {model or 'loading…'})."
            time.sleep(2)

        return (
            "Colibri server launch requested but did not respond within "
            f"{wait_seconds}s. Check 'c/coli status' for details."
        )

    def stop_server(self) -> str:
        """Attempt to stop the Colibri server."""
        coli = self._find_coli()
        if not coli:
            return "coli executable not found. Cannot stop server automatically."
        try:
            result = subprocess.run(
                [str(coli), "stop"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(_COLIBRI_ROOT),
            )
            return result.stdout.strip() or "Colibri stop command sent."
        except Exception as exc:
            return f"Failed to stop Colibri: {exc}"

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _find_coli() -> Optional[Path]:
        """Locate the coli executable (Windows .cmd or POSIX script)."""
        candidates = [_COLI_CMD, _COLI_SCRIPT]
        for p in candidates:
            if p.exists():
                return p
        # Also check PATH
        import shutil
        found = shutil.which("coli") or shutil.which("coli.cmd")
        return Path(found) if found else None

    def start_guide(self) -> str:
        """Return a human-friendly guide on how to start Colibri."""
        return (
            "**Colibri Setup Guide**\n\n"
            "Colibri is a local LLM engine that runs large models on your CPU/GPU.\n\n"
            "**Windows (quick start)**:\n"
            "  1. Open `colibri-main\\` in File Explorer.\n"
            "  2. Double-click `START-HERE.bat`.\n"
            "  3. Follow the on-screen prompts to select a model.\n\n"
            "**Command line**:\n"
            "```\n"
            "cd colibri-main\n"
            ".\\START-HERE.bat          # Windows\n"
            "./start-here.sh            # Linux / macOS\n"
            "```\n\n"
            "Once running, Charlie will use it automatically at http://127.0.0.1:8000/v1\n\n"
            "**Available engines** (all run from disk, no GPU required):\n"
            "  GLM-5.2 (744B MoE), DeepSeek V4 Flash, Qwen3.6, OLMoE, MiMo, and more."
        )

    def status(self) -> str:
        """Return a human-readable status string."""
        if not self.is_server_running():
            return (
                "Colibri server is **not running**.\n\n"
                f"Start it with: `START-HERE.bat` inside `{_COLIBRI_ROOT.name}`"
            )
        models = self.get_models(refresh=True)
        model_list = "\n".join(f"  - {m}" for m in models) if models else "  (none loaded yet)"
        return (
            f"Colibri server is **running** at {self.base_url}\n\n"
            f"Available models:\n{model_list}"
        )

    # ------------------------------------------------------------------ describe
    @property
    def available(self) -> bool:
        """True when server is reachable."""
        return self.is_server_running()

    def describe(self) -> str:
        if self.is_server_running():
            model = self.active_model() or "loading"
            return (
                f"Colibri local LLM engine (running, model: {model}).\n"
                "Provides high-quality inference without cloud API keys."
            )
        return (
            "Colibri local LLM engine (not running).\n"
            "Run START-HERE.bat in colibri-main/ to start."
        )
