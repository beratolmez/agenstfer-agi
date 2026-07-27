from pathlib import Path
import pytest
from fastapi import HTTPException

from agi_server.main import DBTestRequest, MCPTestRequest, source_test_db, source_test_mcp
from agi_server.db import Base, create_engine, sessionmaker


def test_source_test_db_unreachable_host_raises_400():
    payload = DBTestRequest(
        db_type="postgresql",
        host="10.255.255.1",
        port=1,
        database_name="nonexistent",
        username="user",
        password="pwd",
    )
    with pytest.raises(HTTPException) as exc_info:
        source_test_db(payload, db=None, actor=None)
    assert exc_info.value.status_code == 400
    assert "Veritabanı sunucusuna erişilemedi" in exc_info.value.detail


def test_source_test_db_sqlite_real_introspection(tmp_path: Path):
    db_file = tmp_path / "sample.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)
    engine.dispose()

    payload = DBTestRequest(
        db_type="sqlite",
        host="localhost",
        port=0,
        database_name=str(db_file),
        username="",
        password="",
    )
    result = source_test_db(payload, db=None, actor=None)
    assert result["status"] == "connected"
    assert isinstance(result["tables_found"], list)
    assert "users" in result["tables_found"]


def test_source_test_mcp_unreachable_raises_400():
    payload = MCPTestRequest(mcp_url="http://localhost:59999/mcp")
    with pytest.raises(HTTPException) as exc_info:
        source_test_mcp(payload, db=None, actor=None)
    assert exc_info.value.status_code == 400
    assert "MCP sunucusuna erişilemedi" in exc_info.value.detail
