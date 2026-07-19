import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.app.database import Base, get_db
from src.backend.app.main import create_app
from src.backend.app.models.entities import TicketPriority, TicketStatus, User, UserRole


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def users(db_session):
    alice = User(name="Alice", email="alice@test.com", role=UserRole.ADMIN)
    bob = User(name="Bob", email="bob@test.com", role=UserRole.AGENT)
    db_session.add_all([alice, bob])
    db_session.commit()
    db_session.refresh(alice)
    db_session.refresh(bob)
    return {"alice": alice, "bob": bob}


@pytest.fixture()
def open_ticket(client, users):
    response = client.post(
        "/api/tickets",
        json={
            "title": "Test ticket",
            "description": "A test ticket",
            "priority": TicketPriority.MEDIUM.value,
            "created_by": users["alice"].id,
            "assigned_to": users["bob"].id,
        },
    )
    assert response.status_code == 201
    return response.json()
