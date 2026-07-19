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
