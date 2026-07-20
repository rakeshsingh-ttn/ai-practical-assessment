import pytest

from src.backend.app.auth.passwords import DEFAULT_SEED_PASSWORD
from tests.helpers import assert_error_response


def test_login_success(client, users):
    response = client.post(
        "/api/auth/login",
        json={"email": users["alice"].email, "password": DEFAULT_SEED_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_invalid_password_returns_401(client, users):
    response = client.post(
        "/api/auth/login",
        json={"email": users["alice"].email, "password": "wrong-password"},
    )
    error = assert_error_response(response, status_code=401, code="unauthorized")
    assert error["message"] == "Invalid email or password"


def test_login_unknown_email_returns_401(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": DEFAULT_SEED_PASSWORD},
    )
    assert_error_response(response, status_code=401, code="unauthorized")


def test_login_rejects_extra_fields(client, users):
    response = client.post(
        "/api/auth/login",
        json={
            "email": users["alice"].email,
            "password": DEFAULT_SEED_PASSWORD,
            "remember_me": True,
        },
    )
    assert_error_response(response, status_code=422, code="validation_error")


def test_me_returns_current_user(client, users):
    login = client.post(
        "/api/auth/login",
        json={"email": users["bob"].email, "password": DEFAULT_SEED_PASSWORD},
    )
    token = login.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == users["bob"].id
    assert data["email"] == users["bob"].email
    assert data["role"] == "Agent"


def test_me_without_token_returns_401(client):
    response = client.get("/api/auth/me")
    assert_error_response(response, status_code=401, code="unauthorized")


def test_me_invalid_token_returns_401(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-valid-token"})
    assert_error_response(response, status_code=401, code="unauthorized")


@pytest.mark.parametrize(
    "method,path,json_body",
    [
        ("post", "/api/tickets", {"title": "No auth", "description": "d", "priority": "Medium"}),
        ("patch", "/api/tickets/{ticket_id}", {"title": "No auth edit"}),
        ("post", "/api/tickets/{ticket_id}/status", {"status": "In Progress"}),
        ("post", "/api/tickets/{ticket_id}/comments", {"message": "No auth comment"}),
    ],
)
def test_mutating_endpoints_require_auth(client, open_ticket, method, path, json_body):
    resolved_path = path.format(ticket_id=open_ticket["id"])
    response = getattr(client, method)(resolved_path, json=json_body)
    assert_error_response(response, status_code=401, code="unauthorized")


@pytest.mark.parametrize(
    "method,path,json_body",
    [
        ("post", "/api/tickets", {"title": "Bad token", "description": "d", "priority": "Medium"}),
        ("patch", "/api/tickets/{ticket_id}", {"title": "Bad token edit"}),
        ("post", "/api/tickets/{ticket_id}/status", {"status": "In Progress"}),
        ("post", "/api/tickets/{ticket_id}/comments", {"message": "Bad token comment"}),
    ],
)
def test_mutating_endpoints_reject_invalid_token(client, open_ticket, method, path, json_body):
    resolved_path = path.format(ticket_id=open_ticket["id"])
    headers = {"Authorization": "Bearer invalid-token"}
    response = getattr(client, method)(resolved_path, json=json_body, headers=headers)
    assert_error_response(response, status_code=401, code="unauthorized")


def test_read_endpoints_remain_public(client, open_ticket, users):
    assert client.get("/api/tickets").status_code == 200
    assert client.get(f"/api/tickets/{open_ticket['id']}").status_code == 200
    assert client.get(f"/api/tickets/{open_ticket['id']}/comments").status_code == 200
    assert client.get("/api/users").status_code == 200


def test_export_requires_auth(client):
    response = client.get("/api/tickets/export")
    assert_error_response(response, status_code=401, code="unauthorized")


def test_export_scoped_to_authenticated_user(authed, agent_authed, users, open_ticket):
    """Alice's ticket must not appear in Bob's export."""
    alice_export = authed.get("/api/tickets/export")
    assert alice_export.status_code == 200
    assert "Test ticket" in alice_export.text

    bob_export = agent_authed.get("/api/tickets/export")
    assert bob_export.status_code == 200
    assert "Test ticket" not in bob_export.text
    assert bob_export.text.strip().splitlines()[0].startswith("id,title,description")


def test_forbidden_error_shape(requester_authed, open_ticket):
    response = requester_authed.patch(
        f"/api/tickets/{open_ticket['id']}",
        json={"title": "Forbidden edit"},
    )
    error = assert_error_response(response, status_code=403, code="forbidden")
    assert "own tickets" in error["message"].lower()
