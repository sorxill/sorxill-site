"""Иерархия доменных ошибок. Слой API превращает их в problem+json."""


class DomainError(Exception):
    """Базовая ошибка предметной области."""

    code = "domain_error"
    status = 400


class ValidationError(DomainError):
    code = "validation_failed"
    status = 422


class NotFoundError(DomainError):
    code = "not_found"
    status = 404


class InvariantError(DomainError):
    code = "invariant_violated"
    status = 409
