from pathlib import Path

import pytest

from models.model import InferenceError, ModelInfo, ModelManager


def _manager(tmp_path, **config):
    values = {
        "model_directories": [str(tmp_path)],
        "discover_existing_model_blobs": False,
        **config,
    }
    return ModelManager(values)


def test_nested_llama_settings_are_honoured(tmp_path):
    manager = _manager(tmp_path, llama={"context_size": 1024, "timeout_seconds": 9})

    assert manager.settings.context_size == 1024
    assert manager.settings.timeout_seconds == 9


def test_missing_explicit_complex_route_does_not_silently_fallback(tmp_path):
    (tmp_path / "tinyllama.gguf").write_bytes(b"GGUFtest")
    manager = _manager(
        tmp_path,
        default_model="tinyllama",
        model_routing={"complex": "gemma-3-4b-it"},
    )

    assert manager.resolve_model_name("complex") is None
    with pytest.raises(InferenceError, match="configured complex model"):
        manager.load_model(task="complex")


def test_tinyllama_and_gemma_prompts_use_their_chat_templates():
    messages = [{"role": "system", "content": "Be concise."}, {"role": "user", "content": "Hello"}]

    tiny = ModelManager.format_chat_prompt(messages, model_name="tinyllama-1.1b")
    gemma = ModelManager.format_chat_prompt(messages, model_name="gemma-3-4b-it")

    assert "<|system|>" in tiny and "<|assistant|>" in tiny
    assert "<start_of_turn>user" in gemma and "<start_of_turn>model" in gemma


def test_loading_a_second_model_evicts_the_first_by_default(tmp_path, monkeypatch):
    first = tmp_path / "tinyllama.gguf"
    second = tmp_path / "gemma.gguf"
    first.write_bytes(b"GGUFone")
    second.write_bytes(b"GGUFtwo")
    manager = _manager(tmp_path)

    class FakeEngine:
        def __init__(self, path, settings):
            self.path = path
            self.unloaded = False

        def unload(self):
            self.unloaded = True

    monkeypatch.setattr("models.model.LlamaCppEngine", FakeEngine)
    manager.load_model("tinyllama")
    first_engine = manager.engines["tinyllama"]
    manager.load_model("gemma")

    assert list(manager.engines) == ["gemma"]
    assert first_engine.unloaded is True
