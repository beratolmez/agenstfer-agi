from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class TriggerRule:
    id: str
    name: str
    event_type: str
    target_workflow_id: str
    description: str
    enabled: bool = True


DEFAULT_TRIGGER_RULES = [
    TriggerRule(
        id="trig-growth-diagnostic",
        name="Growth Opportunity Signal -> Built-in Diagnostic Workflow",
        event_type="growth.opportunity_detected",
        target_workflow_id="builtin-growth-diagnostic",
        description="Fires standard growth diagnostic workflow on market opportunity signals.",
        enabled=True,
    ),
    TriggerRule(
        id="trig-crm-hygiene",
        name="CRM Record Changed -> Data Hygiene Workflow",
        event_type="crm.account_updated",
        target_workflow_id="builtin-crm-erp-hygiene",
        description=(
            "Fires automatic entity reconciliation and data validation when a CRM account"
            " is updated."
        ),
        enabled=True,
    ),
    TriggerRule(
        id="trig-inbound-triage",
        name="Inbound Lead Form -> Intent Triage Workflow",
        event_type="inbound.form_submitted",
        target_workflow_id="builtin-inbound-triage",
        description="Extracts buyer intent, computes lead score, and prepares sales routing.",
        enabled=True,
    ),
    TriggerRule(
        id="trig-battlecard-gen",
        name="Competitor Intelligence Signal -> Battlecard Generator",
        event_type="competitor.signal_detected",
        target_workflow_id="builtin-competitive-battlecard",
        description=(
            "Generates executive battlecard and objection handling matrix on new"
            " competitor moves."
        ),
        enabled=True,
    ),
    TriggerRule(
        id="trig-lead-discovery",
        name="Market Signal Event -> Lead Discovery Workflow",
        event_type="lead.opportunity_detected",
        target_workflow_id="builtin-lead-discovery",
        description="Discovers matching target B2B accounts and produces opportunity hypotheses.",
        enabled=True,
    ),
]


class EventTriggerEngine:
    def __init__(self):
        self._rules = {rule.id: rule for rule in DEFAULT_TRIGGER_RULES}
        self._event_log: list[dict[str, Any]] = []

    def get_rules(self) -> list[dict[str, Any]]:
        return [
            {
                "id": rule.id,
                "name": rule.name,
                "event_type": rule.event_type,
                "target_workflow_id": rule.target_workflow_id,
                "description": rule.description,
                "enabled": rule.enabled,
            }
            for rule in self._rules.values()
        ]

    def record_event(
        self, source_id: str, event_type: str, payload: dict[str, Any], status: str = "received"
    ) -> dict[str, Any]:
        event_item = {
            "id": f"evt-{len(self._event_log) + 1:04d}",
            "source_id": source_id,
            "event_type": event_type,
            "payload": payload,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._event_log.append(event_item)
        return event_item

    def match_rules(self, event_type: str) -> list[TriggerRule]:
        return [
            rule for rule in self._rules.values()
            if rule.enabled and rule.event_type == event_type
        ]

    def get_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(self._event_log[-limit:]))


trigger_engine = EventTriggerEngine()
