"""Diagnostic helpers shared by the workflow runtime.

The orchestration itself lives in ``agi_server.workflow``; this package provides the
evidence gate, claim construction and report artifact writing that the workflow nodes use.
"""

from agi_server.diagnostics.service import EvidenceGateResult

__all__ = ["EvidenceGateResult"]
