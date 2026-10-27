class ServiceError(Exception):
    """A business-rule or persistence error that can be translated at the API boundary."""


class RecordNotFound(ServiceError):
    pass


class Conflict(ServiceError):
    pass


class InvalidOperation(ServiceError):
    pass

