from core.complexity import ComplexityRouter


def test_simple_chat_uses_tinyllama_route():
    decision = ComplexityRouter().classify("Can you explain what a variable is?")
    assert decision.task == "simple"
    assert decision.level == "simple"


def test_analytical_request_uses_complex_route():
    decision = ComplexityRouter().classify("Compare two approaches and explain the trade-offs.")
    assert decision.task == "complex"
    assert decision.reason == "analytical request"


def test_long_request_uses_complex_route():
    decision = ComplexityRouter({"long_request_chars": 20}).classify("This is a deliberately long request.")
    assert decision.task == "complex"
    assert decision.reason == "long request"


def test_multi_step_request_uses_complex_route():
    decision = ComplexityRouter().classify("First inspect it, then plan it, and finally explain it.")
    assert decision.task == "complex"
    assert decision.reason == "multi-step request"


def test_structured_multiline_payload_uses_complex_route():
    decision = ComplexityRouter().classify("name: Charlie\nrole: local assistant")
    assert decision.task == "complex"
    assert decision.reason == "code or structured payload"
