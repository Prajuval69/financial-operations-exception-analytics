import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import init_db, make_engine, session_scope
from app.main import create_app
from app.services.generator import GeneratorConfig
from app.services.ingestion import seed_dataset
from app.services.validation import run_validation


@pytest.fixture
def policy():
    return Settings(database_url="sqlite:///:memory:")


@pytest.fixture
def engine(policy):
    engine = make_engine(policy)
    init_db(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(engine, policy, tmp_path):
    policy.output_dir = tmp_path
    with session_scope(engine) as session:
        seed_dataset(session, GeneratorConfig(rows=250, accounts=25))
        run_validation(session, policy)
    with TestClient(create_app(policy, engine)) as test_client:
        yield test_client
