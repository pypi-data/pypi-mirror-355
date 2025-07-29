from __future__ import annotations

from collections.abc import Iterable
from typing import override

from pygoerrors.helpers import Nil, NilType
from pygoerrors.protocols import Error, WrappedError


def new(message: str) -> Error:
    """
    Create a new error

    Args:
        message: The error message

    Returns:
        The new error
    """
    return stringError(message)


def _is(err: Error, target: Error) -> bool:
    """
    Check if the error is the same. This uses unwrap to recursively unwrap the error

    Args:
        err: The error to compare
        target: The target error to look for

    Returns:
        Whether the error is the same
    """
    while True:
        if err == target:
            return True

        if isinstance(err, WrappedError):
            err = err.unwrap()
            if not err:
                return False
        else:
            return False


def is_(err: Error, target: Error) -> bool:
    """
    Check if the error is the same. This uses unwrap to recursively unwrap the error

    Args:
        err: The error to compare
        target: The target error to look for

    Returns:
        Whether the error is the same
    """
    if not err or not target:
        return err == target

    return _is(err, target)


def as_[T: Error](err: Error, target: type[T]) -> T | NilType:
    """
    Return the error as the target type

    Args:
        err: The error to convert as the target type
        target: The target type

    Returns:
        The error as the target type
    """
    if not err:
        return Nil

    while True:
        if isinstance(err, target):
            return err

        if isinstance(err, WrappedError):
            err = err.unwrap()
            if not err:
                return Nil
        else:
            return Nil


def join(*errs: Error) -> Error:
    """
    Returns an error that contains all the errors or Nil if all errors are Nil

    Args:
        errs: The errors to join

    Returns:
        The joined errors
    """
    filtered_errors = filter(lambda e: e, errs)
    errors = list(filtered_errors)

    if len(errors) == 0:
        return Nil

    return jsonError(errors)


class stringError(Error):
    def __init__(self, error: str):
        self.__error = error

    @override
    def error(self) -> str:
        return self.__error


class jsonError(Error):
    def __init__(self, errs: Iterable[Error]):
        self.__errs = errs

    @override
    def error(self) -> str:
        return "\n".join(map(lambda e: e.error(), self.__errs))


class wrappedError(Error, WrappedError):
    def __init__(self, msg: str, error: Error):
        self.__message = msg
        self.__error = error

    @override
    def unwrap(self) -> Error:
        return self.__error

    @override
    def error(self) -> str:
        return self.__message
