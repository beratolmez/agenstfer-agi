from pathlib import Path
from sqlalchemy.engine import make_url
from agi_server.config import Settings
from agi_server.db import create_engine, SessionLocal, Base


def test_sqlite_url_parent_directory_resolution(tmp_path: Path):
    db_file = tmp_path / "subdir" / "test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    
    url = make_url(db_url)
    assert url.database is not None
    db_path = Path(url.database)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    assert db_path.parent.exists()

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    engine.dispose()
