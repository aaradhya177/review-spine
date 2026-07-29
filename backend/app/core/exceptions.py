class ReviewSpineError(Exception):
    """Base exception for expected Review Spine failures."""


class ConfigurationError(ReviewSpineError):
    """Raised when runtime configuration is invalid."""


class ExternalServiceError(ReviewSpineError):
    """Raised when an external dependency fails."""


class IdempotencyConflictError(ReviewSpineError):
    """Raised when an operation conflicts with a previous idempotency record."""

