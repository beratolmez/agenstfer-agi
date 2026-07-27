from agi_server.workflow.triggers import trigger_engine


def test_trigger_rule_registry():
    rules = trigger_engine.get_rules()
    assert len(rules) >= 4

    event_types = {r["event_type"] for r in rules}
    assert "growth.opportunity_detected" in event_types
    assert "inbound.form_submitted" in event_types
    assert "crm.account_updated" in event_types
    assert "competitor.signal_detected" in event_types
    assert "lead.opportunity_detected" in event_types


def test_match_rules_and_record_event():
    matched = trigger_engine.match_rules("growth.opportunity_detected")
    assert len(matched) == 1
    assert matched[0].target_workflow_id == "builtin-growth-diagnostic"

    evt = trigger_engine.record_event(
        source_id="src-crm-001",
        event_type="growth.opportunity_detected",
        payload={"lead_name": "Test Co", "intent_score": 90},
        status="triggered",
    )
    assert evt["id"].startswith("evt-")
    assert evt["source_id"] == "src-crm-001"
    assert evt["status"] == "triggered"

    events = trigger_engine.get_events(limit=10)
    assert len(events) >= 1
    assert events[0]["id"] == evt["id"]
