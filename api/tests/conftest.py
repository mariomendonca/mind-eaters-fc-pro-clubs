import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import connect, init_schema


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def conn(db_path):
    c = connect(db_path)
    init_schema(c)
    yield c
    c.close()


@pytest.fixture
def client(db_path, conn):
    from app.main import create_app

    app = create_app(Settings(db_path=db_path, collector_enabled=False))
    with TestClient(app) as c:
        yield c
