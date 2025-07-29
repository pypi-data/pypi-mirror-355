from typing import Protocol, override, runtime_checkable


@runtime_checkable
class Error(Protocol):
    """The error protocol, all errors must implement this protocol"""

    def error(self) -> str: ...

    @override
    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, Error):
            return False

        return self.error() == value.error()

    @override
    def __str__(self) -> str:
        return self.error()

    @override
    def __repr__(self) -> str:
        return self.error()


@runtime_checkable
class WrappedError(Protocol):
    def unwrap(self) -> Error: ...


type Result[T] = tuple[T, Error]
