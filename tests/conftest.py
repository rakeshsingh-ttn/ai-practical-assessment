import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.app.database import Base, get_db
from src.backend.app.main import create_app
from src.backend.app.models.entities import TicketPriority, TicketStatus, User, UserRole
from src.backend.app.auth.passwords import DEFAULT_SEED_PASSWORD, hash_password


def login_headers(client: TestClient, user: User) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": DEFAULT_SEED_PASSWORD},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class AuthedClient:
    """TestClient wrapper that attaches Bearer auth to mutating requests."""

    def __init__(self, client: TestClient, headers: dict[str, str]):
        self._client = client
        self._headers = headers

    def _merge_headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        merged = dict(self._headers)
        if headers:
            merged.update(headers)
        return merged

    def get(self, url: str, **kwargs):
        kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
        return self._client.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
        return self._client.post(url, **kwargs)

    def patch(self, url: str, **kwargs):
        kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
        return self._client.patch(url, **kwargs)


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
    password_hash = hash_password(DEFAULT_SEED_PASSWORD)
    alice = User(
        name="Alice",
        email="alice@test.com",
        role=UserRole.ADMIN,
        password_hash=password_hash,
    )
    bob = User(
        name="Bob",
        email="bob@test.com",
        role=UserRole.AGENT,
        password_hash=password_hash,
    )
    dave = User(
        name="Dave",
        email="dave@test.com",
        role=UserRole.REQUESTER,
        password_hash=password_hash,
    )
    carol = User(
        name="Carol",
        email="carol@test.com",
        role=UserRole.MANAGER,
        password_hash=password_hash,
    )
    db_session.add_all([alice, bob, dave, carol])
    db_session.commit()
    db_session.refresh(alice)
    db_session.refresh(bob)
    db_session.refresh(dave)
    db_session.refresh(carol)
    return {"alice": alice, "bob": bob, "dave": dave, "carol": carol}


@pytest.fixture()
def auth_headers(client, users):
    return login_headers(client, users["alice"])


@pytest.fixture()
def requester_headers(client, users):
    return login_headers(client, users["dave"])


@pytest.fixture()
def authed(client, auth_headers):
    return AuthedClient(client, auth_headers)


@pytest.fixture()
def requester_authed(client, requester_headers):
    return AuthedClient(client, requester_headers)


@pytest.fixture()
def agent_headers(client, users):
    return login_headers(client, users["bob"])


@pytest.fixture()
def agent_authed(client, agent_headers):
    return AuthedClient(client, agent_headers)


@pytest.fixture()
def manager_headers(client, users):
    return login_headers(client, users["carol"])


@pytest.fixture()
def manager_authed(client, manager_headers):
    return AuthedClient(client, manager_headers)


@pytest.fixture()
def open_ticket(authed, users):
    response = authed.post(
        "/api/tickets",
        json={
            "title": "Test ticket",
            "description": "A test ticket",
            "priority": TicketPriority.MEDIUM.value,
            "assigned_to": users["bob"].id,
        },
    )
    assert response.status_code == 201
    return response.json()
