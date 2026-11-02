from core.complexity import ComplexityRouter


class _ModelManager:
    def __init__(self):
        self.calls = []

    def chat(self, messages, *, task="general"):
        self.calls.append((messages, task))
        return "model reply"

    def resolve_model_name(self, task="general"):
        return "tinyllama" if task == "simple" else "gemma-3-4b-it"


def _assistant_with_router():
    from core.assistant import OfflineAssistant

    assistant = OfflineAssistant.__new__(OfflineAssistant)
    assistant.model_manager = _ModelManager()
    assistant.complexity_router = ComplexityRouter()
    assistant.last_model_route = None
    assistant.last_model_name = None
    assistant.colibri = None
    assistant.config = type("Config", (), {"get": lambda _self, _key, default=None: default})()
    assistant.memory = None
    assistant.conversation_history = []
    return assistant


def test_simple_freeform_chat_uses_simple_model_route():
    assistant = _assistant_with_router()
    assert assistant._chat("Tell me a short joke.") == "model reply"
    assert assistant.model_manager.calls[0][1] == "simple"
    assert assistant.last_model_route.reason == "conversational request"
    assert assistant.last_model_name == "tinyllama"


def test_complex_freeform_chat_uses_complex_model_route():
    assistant = _assistant_with_router()
    assert assistant._chat("Compare these approaches and explain the trade-offs.") == "model reply"
    assert assistant.model_manager.calls[0][1] == "complex"
    assert assistant.last_model_route.reason == "analytical request"


def test_ready_colibri_is_preferred_over_gguf_models():
    class Colibri:
        available = True

        @staticmethod
        def active_model():
            return "qwen-colibri"

        @staticmethod
        def chat_messages(messages):
            assert messages[-1]["content"] == "Tell me about local inference."
            return "colibri reply"

    assistant = _assistant_with_router()
    assistant.colibri = Colibri()

    assert assistant._chat("Tell me about local inference.") == "colibri reply"
    assert assistant.model_manager.calls == []
    assert assistant.last_model_name == "Colibri · qwen-colibri"
