class DomainError(Exception):
    """Base class for all engine/domain errors."""


class BettingClosed(DomainError):
    pass


class InsufficientCredits(DomainError):
    pass


class StakeOutOfRange(DomainError):
    pass


class AlreadySettled(DomainError):
    pass


class InvalidSelection(DomainError):
    pass


class NotFound(DomainError):
    pass
