from observation_plane.privacy_gate import apply_privacy_gate


def _raw_span(**attribute_overrides):
    attributes = {"run_id": "run_abc123", "agent_name": "Sales Research Agent"}
    attributes.update(attribute_overrides)
    return {
        "trace_id": "a5aa9f441d040ce59366023d09b1bee8",
        "span_id": "926c58404ec62bf6",
        "parent_span_id": "06023765beb0c92a",
        "name": "agent.step",
        "start_time": "2026-09-14T15:00:00Z",
        "end_time": "2026-09-14T15:00:01Z",
        "status": "UNSET",
        "attributes": attributes,
    }


def test_allowed_attributes_pass_through_unchanged():
    event = apply_privacy_gate(_raw_span())

    assert event.attributes["run_id"] == "run_abc123"
    assert event.attributes["agent_name"] == "Sales Research Agent"


def test_normalizes_the_span_shape():
    event = apply_privacy_gate(_raw_span())

    assert event.trace_id == "a5aa9f441d040ce59366023d09b1bee8"
    assert event.span_id == "926c58404ec62bf6"
    assert event.parent_span_id == "06023765beb0c92a"
    assert event.name == "agent.step"


def test_an_attribute_not_on_the_allowlist_is_dropped_entirely():
    event = apply_privacy_gate(_raw_span(customer_email="alice@example.com", internal_debug_dump="raw prompt text..."))

    assert "customer_email" not in event.attributes
    assert "internal_debug_dump" not in event.attributes
    # the allowed ones are still there
    assert "run_id" in event.attributes


def test_an_email_accidentally_inside_an_allowed_field_is_redacted_not_dropped():
    event = apply_privacy_gate(_raw_span(agent_name="Contact bob@company.com for details"))

    assert "bob@company.com" not in event.attributes["agent_name"]
    assert "[REDACTED_EMAIL]" in event.attributes["agent_name"]


def test_an_api_key_shaped_string_is_redacted():
    event = apply_privacy_gate(_raw_span(agent_name="key sk-abcdefghijklmnopqrstuvwx leaked"))

    assert "sk-abcdefghijklmnopqrstuvwx" not in event.attributes["agent_name"]
    assert "[REDACTED_SECRET]" in event.attributes["agent_name"]


def test_a_credit_card_shaped_number_is_redacted():
    event = apply_privacy_gate(_raw_span(agent_name="card 4111111111111111 on file"))

    assert "4111111111111111" not in event.attributes["agent_name"]
    assert "[REDACTED_NUMBER]" in event.attributes["agent_name"]


def test_root_span_with_no_parent_normalizes_parent_span_id_to_none():
    raw = _raw_span()
    del raw["parent_span_id"]

    event = apply_privacy_gate(raw)

    assert event.parent_span_id is None
