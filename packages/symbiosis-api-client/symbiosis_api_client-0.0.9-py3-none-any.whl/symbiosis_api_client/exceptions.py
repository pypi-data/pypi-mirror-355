"""Exceptions  for the Symbiosis API Client."""


class ChainNotFound(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class TokenNotFound(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ChainNotInSwap(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class SwapRoutNotExist(Exception): ...


class InvalidCommit(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class SwapCreationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
