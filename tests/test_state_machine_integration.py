import pytest

from src.backend.app.models.entities import TicketStatus


class TestStateMachineIntegration:
    def _transition(self, client, ticket_id, status):
        return client.post(f"/api/tickets/{ticket_id}/status", json={"status": status})

    def test_full_valid_lifecycle(self, client, open_ticket):
        ticket_id = open_ticket["id"]

        r = self._transition(client, ticket_id, TicketStatus.IN_PROGRESS.value)
        assert r.status_code == 200
        assert r.json()["status"] == TicketStatus.IN_PROGRESS.value

        r = self._transition(client, ticket_id, TicketStatus.RESOLVED.value)
        assert r.status_code == 200
        assert r.json()["status"] == TicketStatus.RESOLVED.value

        r = self._transition(client, ticket_id, TicketStatus.CLOSED.value)
        assert r.status_code == 200
        assert r.json()["status"] == TicketStatus.CLOSED.value

    def test_open_to_cancelled(self, client, open_ticket):
        r = self._transition(client, open_ticket["id"], TicketStatus.CANCELLED.value)
        assert r.status_code == 200
        assert r.json()["status"] == TicketStatus.CANCELLED.value

    def test_in_progress_to_cancelled(self, client, open_ticket):
        ticket_id = open_ticket["id"]
        self._transition(client, ticket_id, TicketStatus.IN_PROGRESS.value)
        r = self._transition(client, ticket_id, TicketStatus.CANCELLED.value)
        assert r.status_code == 200
        assert r.json()["status"] == TicketStatus.CANCELLED.value

    @pytest.mark.parametrize(
        "setup_statuses,target",
        [
            ([], TicketStatus.RESOLVED.value),
            ([], TicketStatus.CLOSED.value),
            ([TicketStatus.IN_PROGRESS.value], TicketStatus.OPEN.value),
            ([TicketStatus.IN_PROGRESS.value], TicketStatus.CLOSED.value),
            (
                [TicketStatus.IN_PROGRESS.value, TicketStatus.RESOLVED.value],
                TicketStatus.IN_PROGRESS.value,
            ),
            (
                [TicketStatus.IN_PROGRESS.value, TicketStatus.RESOLVED.value],
                TicketStatus.CANCELLED.value,
            ),
        ],
    )
    def test_invalid_transitions_from_open_or_in_progress(
        self, client, open_ticket, setup_statuses, target
    ):
        ticket_id = open_ticket["id"]
        for status in setup_statuses:
            self._transition(client, ticket_id, status)

        r = self._transition(client, ticket_id, target)
        assert r.status_code == 409
        body = r.json()
        assert body["error"]["code"] == "invalid_transition"

    def test_no_transitions_from_closed(self, client, open_ticket):
        ticket_id = open_ticket["id"]
        for status in [
            TicketStatus.IN_PROGRESS.value,
            TicketStatus.RESOLVED.value,
            TicketStatus.CLOSED.value,
        ]:
            self._transition(client, ticket_id, status)

        for target in [
            TicketStatus.OPEN.value,
            TicketStatus.IN_PROGRESS.value,
            TicketStatus.RESOLVED.value,
            TicketStatus.CANCELLED.value,
        ]:
            r = self._transition(client, ticket_id, target)
            assert r.status_code == 409
            assert r.json()["error"]["code"] == "invalid_transition"

    def test_no_transitions_from_cancelled(self, client, open_ticket):
        ticket_id = open_ticket["id"]
        self._transition(client, ticket_id, TicketStatus.CANCELLED.value)

        for target in [
            TicketStatus.OPEN.value,
            TicketStatus.IN_PROGRESS.value,
            TicketStatus.RESOLVED.value,
            TicketStatus.CLOSED.value,
        ]:
            r = self._transition(client, ticket_id, target)
            assert r.status_code == 409
            assert r.json()["error"]["code"] == "invalid_transition"

    def test_status_cannot_be_changed_via_patch(self, client, open_ticket):
        r = client.patch(
            f"/api/tickets/{open_ticket['id']}",
            json={"title": "Updated title", "status": TicketStatus.CLOSED.value},
        )
        assert r.status_code == 200
        assert r.json()["status"] == TicketStatus.OPEN.value

    def test_same_status_noop_rejected(self, client, open_ticket):
        r = client.post(
            f"/api/tickets/{open_ticket['id']}/status",
            json={"status": TicketStatus.OPEN.value},
        )
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "invalid_transition"
