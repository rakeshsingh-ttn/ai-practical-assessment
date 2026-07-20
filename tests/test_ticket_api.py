from src.backend.app.models.entities import TicketStatus


class TestTicketAPI:
    def test_create_ticket_validation(self, client, users):
        r = client.post(
            "/api/tickets",
            json={
                "title": "ab",
                "description": "too short title",
                "priority": "Medium",
                "created_by": users["alice"].id,
            },
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "validation_error"

    def test_create_ticket_invalid_user(self, client):
        r = client.post(
            "/api/tickets",
            json={
                "title": "Valid title",
                "description": "desc",
                "priority": "Medium",
                "created_by": 9999,
            },
        )
        assert r.status_code == 404

    def test_clear_assignee(self, client, open_ticket):
        ticket_id = open_ticket["id"]
        assert open_ticket["assigned_to"] is not None
        r = client.patch(f"/api/tickets/{ticket_id}", json={"assigned_to": None})
        assert r.status_code == 200
        assert r.json()["assigned_to"] is None
        assert r.json()["assignee"] is None

    def test_update_closed_ticket_rejected(self, client, open_ticket):
        ticket_id = open_ticket["id"]
        client.post(f"/api/tickets/{ticket_id}/status", json={"status": TicketStatus.CANCELLED.value})
        r = client.patch(f"/api/tickets/{ticket_id}", json={"title": "New title"})
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "ticket_not_editable"

    def test_update_resolved_ticket_rejected(self, client, open_ticket):
        ticket_id = open_ticket["id"]
        client.post(
            f"/api/tickets/{ticket_id}/status",
            json={"status": TicketStatus.IN_PROGRESS.value},
        )
        client.post(
            f"/api/tickets/{ticket_id}/status",
            json={"status": TicketStatus.RESOLVED.value},
        )
        r = client.patch(f"/api/tickets/{ticket_id}", json={"title": "New title"})
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "ticket_not_editable"

    def test_comment_on_cancelled_rejected(self, client, users, open_ticket):
        ticket_id = open_ticket["id"]
        client.post(f"/api/tickets/{ticket_id}/status", json={"status": TicketStatus.CANCELLED.value})
        r = client.post(
            f"/api/tickets/{ticket_id}/comments",
            json={"message": "Should fail", "created_by": users["alice"].id},
        )
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "comment_not_allowed"

    def test_search_filter(self, client, users):
        client.post(
            "/api/tickets",
            json={
                "title": "UniqueSearchTerm123",
                "description": "findme",
                "priority": "High",
                "created_by": users["alice"].id,
            },
        )
        r = client.get("/api/tickets", params={"q": "uniquesearchterm"})
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        assert any("UniqueSearchTerm123" in t["title"] for t in r.json()["items"])

    def test_csv_export(self, client, users, open_ticket):
        r = client.get("/api/tickets/export", params={"created_by": users["alice"].id})
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        assert "Test ticket" in r.text
        assert "id,title,description" in r.text

    def test_csv_export_header_only_when_no_tickets(self, client, users):
        r = client.get("/api/tickets/export", params={"created_by": users["bob"].id})
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        lines = r.text.strip().splitlines()
        assert len(lines) == 1
        assert lines[0].startswith("id,title,description")

    def test_title_max_length(self, client, users):
        r = client.post(
            "/api/tickets",
            json={
                "title": "x" * 121,
                "description": "desc",
                "priority": "Medium",
                "created_by": users["alice"].id,
            },
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "validation_error"

    def test_description_max_length(self, client, users):
        r = client.post(
            "/api/tickets",
            json={
                "title": "Valid title",
                "description": "x" * 5001,
                "priority": "Medium",
                "created_by": users["alice"].id,
            },
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "validation_error"

    def test_invalid_priority(self, client, users):
        r = client.post(
            "/api/tickets",
            json={
                "title": "Valid title",
                "description": "desc",
                "priority": "Urgent",
                "created_by": users["alice"].id,
            },
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "validation_error"

    def test_invalid_status_value(self, client, open_ticket):
        r = client.post(
            f"/api/tickets/{open_ticket['id']}/status",
            json={"status": "Done"},
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "validation_error"

    def test_comment_empty_message(self, client, users, open_ticket):
        r = client.post(
            f"/api/tickets/{open_ticket['id']}/comments",
            json={"message": "", "created_by": users["alice"].id},
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "validation_error"

    def test_comment_whitespace_only_message(self, client, users, open_ticket):
        r = client.post(
            f"/api/tickets/{open_ticket['id']}/comments",
            json={"message": "   ", "created_by": users["alice"].id},
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "validation_error"

    def test_comment_max_length(self, client, users, open_ticket):
        r = client.post(
            f"/api/tickets/{open_ticket['id']}/comments",
            json={"message": "x" * 2001, "created_by": users["alice"].id},
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "validation_error"

    def test_assignee_must_exist(self, client, users):
        r = client.post(
            "/api/tickets",
            json={
                "title": "Valid title",
                "description": "desc",
                "priority": "Medium",
                "created_by": users["alice"].id,
                "assigned_to": 9999,
            },
        )
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "not_found"

    def test_ticket_must_exist(self, client):
        r = client.get("/api/tickets/9999")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "not_found"

    def test_ticket_comments_require_existing_ticket(self, client, users):
        r = client.get("/api/tickets/9999/comments")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "not_found"

    def test_search_filter_status_priority_and_query(self, client, users):
        client.post(
            "/api/tickets",
            json={
                "title": "FilterTargetTicket",
                "description": "needle in haystack",
                "priority": "High",
                "created_by": users["alice"].id,
            },
        )
        client.post(
            "/api/tickets",
            json={
                "title": "Other ticket",
                "description": "needle but low priority",
                "priority": "Low",
                "created_by": users["alice"].id,
            },
        )

        r = client.get(
            "/api/tickets",
            params={"q": "needle", "status": "Open", "priority": "High"},
        )
        assert r.status_code == 200
        titles = [item["title"] for item in r.json()["items"]]
        assert "FilterTargetTicket" in titles
        assert "Other ticket" not in titles

    def test_internal_error_shape(self, db_session, monkeypatch):
        from fastapi.testclient import TestClient

        from src.backend.app.database import get_db
        from src.backend.app.main import create_app
        from src.backend.app.services import ticket_service

        app = create_app()

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        def boom(*_args, **_kwargs):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(ticket_service, "list_tickets", boom)

        with TestClient(app, raise_server_exceptions=False) as test_client:
            r = test_client.get("/api/tickets")

        assert r.status_code == 500
        body = r.json()
        assert body == {
            "error": {
                "code": "internal_error",
                "message": "Internal server error",
                "details": None,
            }
        }
