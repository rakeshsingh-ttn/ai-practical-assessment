import pytest

from src.backend.app.models.entities import TicketPriority, TicketStatus
from tests.helpers import assert_error_response


class TestRolePermissions:
    @pytest.mark.parametrize("authed_fixture", ["authed", "agent_authed", "manager_authed"])
    def test_staff_roles_can_change_status(self, request, users, authed_fixture):
        client = request.getfixturevalue(authed_fixture)
        created = client.post(
            "/api/tickets",
            json={
                "title": "Status change ticket",
                "description": "desc",
                "priority": TicketPriority.MEDIUM.value,
                "assigned_to": users["bob"].id,
            },
        )
        assert created.status_code == 201
        ticket_id = created.json()["id"]

        response = client.post(
            f"/api/tickets/{ticket_id}/status",
            json={"status": TicketStatus.IN_PROGRESS.value},
        )
        assert response.status_code == 200
        assert response.json()["status"] == TicketStatus.IN_PROGRESS.value

    def test_requester_cannot_change_status(self, requester_authed, open_ticket):
        response = requester_authed.post(
            f"/api/tickets/{open_ticket['id']}/status",
            json={"status": TicketStatus.IN_PROGRESS.value},
        )
        assert_error_response(response, status_code=403, code="forbidden")

    def test_requester_can_create_own_ticket(self, requester_authed, users):
        response = requester_authed.post(
            "/api/tickets",
            json={
                "title": "My own ticket",
                "description": "desc",
                "priority": TicketPriority.LOW.value,
            },
        )
        assert response.status_code == 201
        assert response.json()["created_by"] == users["dave"].id

    def test_requester_cannot_edit_others_ticket(self, requester_authed, open_ticket):
        response = requester_authed.patch(
            f"/api/tickets/{open_ticket['id']}",
            json={"title": "Unauthorized edit"},
        )
        assert_error_response(response, status_code=403, code="forbidden")

    def test_requester_can_edit_own_ticket(self, requester_authed, users):
        created = requester_authed.post(
            "/api/tickets",
            json={
                "title": "Editable ticket",
                "description": "desc",
                "priority": TicketPriority.MEDIUM.value,
            },
        )
        ticket_id = created.json()["id"]

        response = requester_authed.patch(
            f"/api/tickets/{ticket_id}",
            json={"title": "Updated by requester"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated by requester"

    def test_agent_can_edit_others_ticket(self, agent_authed, open_ticket):
        response = agent_authed.patch(
            f"/api/tickets/{open_ticket['id']}",
            json={"title": "Staff edit"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Staff edit"

    def test_requester_cannot_comment_on_others_ticket(self, requester_authed, open_ticket):
        response = requester_authed.post(
            f"/api/tickets/{open_ticket['id']}/comments",
            json={"message": "Not my ticket"},
        )
        assert_error_response(response, status_code=403, code="forbidden")

    def test_agent_can_comment_on_others_ticket(self, agent_authed, users, open_ticket):
        response = agent_authed.post(
            f"/api/tickets/{open_ticket['id']}/comments",
            json={"message": "Staff comment"},
        )
        assert response.status_code == 201
        assert response.json()["message"] == "Staff comment"
        assert response.json()["created_by"] == users["bob"].id

    def test_requester_can_comment_on_own_ticket(self, requester_authed, users):
        created = requester_authed.post(
            "/api/tickets",
            json={
                "title": "Ticket with comment",
                "description": "desc",
                "priority": TicketPriority.MEDIUM.value,
            },
        )
        ticket_id = created.json()["id"]

        response = requester_authed.post(
            f"/api/tickets/{ticket_id}/comments",
            json={"message": "My comment"},
        )
        assert response.status_code == 201
        assert response.json()["message"] == "My comment"
        assert response.json()["created_by"] == users["dave"].id

    def test_create_rejects_created_by_field(self, authed, users):
        response = authed.post(
            "/api/tickets",
            json={
                "title": "Spoofed creator",
                "description": "desc",
                "priority": TicketPriority.MEDIUM.value,
                "created_by": users["dave"].id,
            },
        )
        assert_error_response(response, status_code=422, code="validation_error")

    def test_comment_rejects_created_by_field(self, requester_authed, users):
        created = requester_authed.post(
            "/api/tickets",
            json={
                "title": "Own ticket",
                "description": "desc",
                "priority": TicketPriority.MEDIUM.value,
            },
        )
        ticket_id = created.json()["id"]

        response = requester_authed.post(
            f"/api/tickets/{ticket_id}/comments",
            json={"message": "Spoofed author", "created_by": users["alice"].id},
        )
        assert_error_response(response, status_code=422, code="validation_error")
