from src.utils.helpers import route_by_guardrail, route_by_auditor


def test_route_by_guardrail_blocks_when_unsafe():
    state = {"is_safe": False}
    assert route_by_guardrail(state) == "end"


def test_route_by_guardrail_continues_when_safe():
    state = {"is_safe": True}
    assert route_by_guardrail(state) == "researcher"


def test_route_by_auditor_ends_on_pass():
    state = {"status": "PASS", "retry_count": 1}
    assert route_by_auditor(state) == "end"


def test_route_by_auditor_retries_on_fail_before_limit():
    state = {"status": "FAIL", "retry_count": 1}
    assert route_by_auditor(state) == "researcher"


def test_route_by_auditor_ends_after_max_retries():
    state = {"status": "FAIL", "retry_count": 3}
    assert route_by_auditor(state) == "end"