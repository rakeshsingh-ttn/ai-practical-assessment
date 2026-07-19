class AppError(Exception):
    def __init__(self, code: str, message: str, details: dict | list | None = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            code="not_found",
            message=f"{resource} not found",
            details={"resource": resource, "id": identifier},
        )


class ConflictError(AppError):
    def __init__(self, code: str, message: str, details: dict | list | None = None):
        super().__init__(code=code, message=message, details=details)


class InvalidTransitionError(ConflictError):
    def __init__(self, current: str, target: str, allowed: list[str]):
        allowed_text = ", ".join(allowed) if allowed else "none"
        super().__init__(
            code="invalid_transition",
            message=(
                f"Cannot transition from '{current}' to '{target}'. "
                f"Allowed transitions: {allowed_text}."
            ),
            details={"current_status": current, "target_status": target, "allowed": allowed},
        )


class TicketNotEditableError(ConflictError):
    def __init__(self, status: str):
        super().__init__(
            code="ticket_not_editable",
            message=f"Ticket cannot be edited in '{status}' status.",
            details={"status": status},
        )


class CommentNotAllowedError(ConflictError):
    def __init__(self, status: str):
        super().__init__(
            code="comment_not_allowed",
            message=f"Comments are not allowed on tickets in '{status}' status.",
            details={"status": status},
        )
