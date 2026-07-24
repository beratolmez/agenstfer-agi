from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from agi_server.db import MCPProfile


class MCPToolResult(BaseModel):
    tool_name: str
    status: str
    output: Any
    server_identity: str
    read_only: bool = True


class MCPGateway:
    """Product-owned, approved, read-only MCP Client Gateway enforcing code-defined allowlists."""

    def __init__(
        self,
        db: Session,
        *,
        transport_override: Callable[[str, str, dict[str, Any]], Any] | None = None,
    ):
        self.db = db
        self.transport_override = transport_override

    def get_approved_profile(self, profile_id_or_identity: str) -> MCPProfile:
        if "://" in profile_id_or_identity or "/" in profile_id_or_identity:
            msg = f"Arbitrary URL rejected as execution authority: {profile_id_or_identity}"
            raise PermissionError(msg)

        stmt = select(MCPProfile).where(
            (MCPProfile.id == profile_id_or_identity)
            | (MCPProfile.server_identity == profile_id_or_identity)
        )
        profile = self.db.scalars(stmt).first()
        if profile is None:
            msg = f"Approved MCP profile not found: {profile_id_or_identity}"
            raise ValueError(msg)
        if not profile.approved or profile.status != "active":
            msg = f"MCP profile {profile.id} is not approved or active"
            raise PermissionError(msg)
        return profile

    def invoke_tool(
        self,
        profile_id: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        cloud: bool = False,
    ) -> MCPToolResult:
        profile = self.get_approved_profile(profile_id)

        if cloud and profile.data_classification in {"confidential", "restricted"}:
            msg = f"Cloud profile cannot execute {profile.data_classification} MCP data"
            raise PermissionError(msg)

        if not profile.read_only:
            raise PermissionError("MCP gateway allows read-only tools only")

        if tool_name not in profile.allowed_tools:
            msg = f"Tool '{tool_name}' is not in approved allowlist for profile {profile.id}"
            raise PermissionError(msg)

        args = arguments or {}

        if self.transport_override:
            output = self.transport_override(profile.server_identity, tool_name, args)
        else:
            output = {
                "result": f"Executed read-only tool '{tool_name}' on {profile.server_identity}",
                "query_args": args,
            }

        return MCPToolResult(
            tool_name=tool_name,
            status="success",
            output=output,
            server_identity=profile.server_identity,
            read_only=True,
        )
