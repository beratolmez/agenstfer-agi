import pytest
from agi_server.db import Base, MCPProfile
from agi_server.mcp import MCPGateway
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


def test_mcp_gateway_approved_profile_execution(db_session: Session):
    profile = MCPProfile(
        id="mcp-crm-hubspot",
        name="HubSpot Read-Only Connector",
        server_identity="hubspot-mcp-server",
        transport_type="stdio",
        allowed_tools=["read_contacts", "get_deal_stages"],
        data_classification="internal",
        read_only=True,
        approved=True,
        status="active",
        configuration={},
    )
    db_session.add(profile)
    db_session.commit()

    def mock_transport(server_id, tool_name, args):
        assert server_id == "hubspot-mcp-server"
        assert tool_name == "read_contacts"
        return {"contacts": [{"id": "c1", "name": "Acme Corp"}]}

    gateway = MCPGateway(db_session, transport_override=mock_transport)
    result = gateway.invoke_tool("mcp-crm-hubspot", "read_contacts", {"limit": 10})

    assert result.status == "success"
    assert result.tool_name == "read_contacts"
    assert result.server_identity == "hubspot-mcp-server"
    assert result.read_only is True
    assert result.output["contacts"][0]["name"] == "Acme Corp"


def test_mcp_gateway_rejects_arbitrary_user_urls(db_session: Session):
    gateway = MCPGateway(db_session)

    with pytest.raises(PermissionError, match="Arbitrary URL rejected"):
        gateway.get_approved_profile("https://malicious-site.com/mcp")

    with pytest.raises(PermissionError, match="Arbitrary URL rejected"):
        gateway.invoke_tool("http://localhost:8080/mcp", "steal_data")


def test_mcp_gateway_rejects_unapproved_or_inactive_profiles(db_session: Session):
    unapproved = MCPProfile(
        id="mcp-unapproved",
        name="Unapproved Profile",
        server_identity="unapproved-server",
        allowed_tools=["read_contacts"],
        approved=False,
        status="active",
        configuration={},
    )
    inactive = MCPProfile(
        id="mcp-inactive",
        name="Inactive Profile",
        server_identity="inactive-server",
        allowed_tools=["read_contacts"],
        approved=True,
        status="disabled",
        configuration={},
    )
    db_session.add_all([unapproved, inactive])
    db_session.commit()

    gateway = MCPGateway(db_session)

    with pytest.raises(PermissionError, match="is not approved or active"):
        gateway.invoke_tool("mcp-unapproved", "read_contacts")

    with pytest.raises(PermissionError, match="is not approved or active"):
        gateway.invoke_tool("mcp-inactive", "read_contacts")


def test_mcp_gateway_rejects_unlisted_tools(db_session: Session):
    profile = MCPProfile(
        id="mcp-erp",
        name="ERP Reader",
        server_identity="erp-mcp-server",
        allowed_tools=["read_invoices"],
        approved=True,
        status="active",
        configuration={},
    )
    db_session.add(profile)
    db_session.commit()

    gateway = MCPGateway(db_session)

    with pytest.raises(PermissionError, match="not in approved allowlist"):
        gateway.invoke_tool("mcp-erp", "delete_invoice")


def test_mcp_gateway_rejects_non_readonly_profiles(db_session: Session):
    write_profile = MCPProfile(
        id="mcp-writer",
        name="Write Profile",
        server_identity="write-server",
        allowed_tools=["write_data"],
        read_only=False,
        approved=True,
        status="active",
        configuration={},
    )
    db_session.add(write_profile)
    db_session.commit()

    gateway = MCPGateway(db_session)

    with pytest.raises(PermissionError, match="allows read-only tools only"):
        gateway.invoke_tool("mcp-writer", "write_data")


def test_mcp_gateway_cloud_confidential_restricted_fail_closed(db_session: Session):
    confidential_profile = MCPProfile(
        id="mcp-confidential",
        name="Confidential Profile",
        server_identity="secret-server",
        allowed_tools=["read_secret_data"],
        data_classification="confidential",
        read_only=True,
        approved=True,
        status="active",
        configuration={},
    )
    db_session.add(confidential_profile)
    db_session.commit()

    gateway = MCPGateway(db_session)

    with pytest.raises(PermissionError, match="Cloud profile cannot execute"):
        gateway.invoke_tool("mcp-confidential", "read_secret_data", cloud=True)
