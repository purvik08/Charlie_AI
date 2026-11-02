from core.complexity import ComplexityRouter


class _ModelManager:
    def __init__(self):
        self.calls = []

    def chat(self, messages, *, task="general"):
        self.calls.append((messages, task))
        return "model reply"


def _assistant_with_router():
    from core.assistant import OfflineAssistant

    assistant = OfflineAssistant.__new__(OfflineAssistant)
    assistant.model_manager = _ModelManager()
    assistant.complexity_router = ComplexityRouter()
    assistant.last_model_route = None
    assistant.memory = None
    assistant.conversation_history = []
    return assistant


def test_simple_freeform_chat_uses_simple_model_route():
    assistant = _assistant_with_router()
    assert assistant._chat("Tell me a short joke.") == "model reply"
    assert assistant.model_manager.calls[0][1] == "simple"
    assert assistant.last_model_route.reason == "conversational request"


def test_complex_freeform_chat_uses_complex_model_route():
    assistant = _assistant_with_router()
    assert assistant._chat("Compare these approaches and explain the trade-offs.") == "model reply"
    assert assistant.model_manager.calls[0][1] == "complex"
    assert assistant.last_model_route.reason == "analytical request"
