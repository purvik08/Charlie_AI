"""
Local LLM Engine Feature for Charlie AI using Colibri.

Integrates the Colibri engine (colibri-main/) which runs very large
mixture-of-experts models (GLM, DeepSeek, Qwen, MiMo, etc.) on local
hardware via an OpenAI-compatible HTTP API server.
"""

from features.local_llm.colibri_adapter import ColibriAdapter

__all__ = ["ColibriAdapter"]
