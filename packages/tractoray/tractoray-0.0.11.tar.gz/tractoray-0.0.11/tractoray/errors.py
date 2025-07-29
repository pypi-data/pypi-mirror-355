class TractorayError(Exception):
    pass


class RunError(TractorayError):
    _message: str


class CoordinatorError(TractorayError):
    _message: str


class RayBootstrapError(TractorayError):
    _message: str
