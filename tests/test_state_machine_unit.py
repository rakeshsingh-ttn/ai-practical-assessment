import pytest

from src.backend.app.models.entities import TicketStatus
from src.backend.app.services.ticket_status import ALLOWED_TRANSITIONS, can_transition


class TestStateMachineUnit:
    @pytest.mark.parametrize(
        "current,target,expected",
        [
            (TicketStatus.OPEN, TicketStatus.IN_PROGRESS, True),
            (TicketStatus.OPEN, TicketStatus.CANCELLED, True),
            (TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, True),
            (TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED, True),
            (TicketStatus.RESOLVED, TicketStatus.CLOSED, True),
            (TicketStatus.OPEN, TicketStatus.RESOLVED, False),
            (TicketStatus.OPEN, TicketStatus.CLOSED, False),
            (TicketStatus.IN_PROGRESS, TicketStatus.OPEN, False),
            (TicketStatus.RESOLVED, TicketStatus.IN_PROGRESS, False),
            (TicketStatus.RESOLVED, TicketStatus.CANCELLED, False),
            (TicketStatus.CLOSED, TicketStatus.OPEN, False),
            (TicketStatus.CLOSED, TicketStatus.IN_PROGRESS, False),
            (TicketStatus.CANCELLED, TicketStatus.OPEN, False),
            (TicketStatus.CANCELLED, TicketStatus.IN_PROGRESS, False),
        ],
    )
    def test_can_transition(self, current, target, expected):
        assert can_transition(current, target) is expected

    def test_allowed_transitions_cover_all_statuses(self):
        assert set(ALLOWED_TRANSITIONS.keys()) == set(TicketStatus)

    def test_terminal_states_have_no_outgoing_transitions(self):
        assert ALLOWED_TRANSITIONS[TicketStatus.CLOSED] == set()
        assert ALLOWED_TRANSITIONS[TicketStatus.CANCELLED] == set()
