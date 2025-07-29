import functools
from collections.abc import Iterable, MutableMapping
from typing import Any, Callable, cast

import cachetools

from pygoerrors.errors import new
from pygoerrors.helpers import Nil
from pygoerrors.iterators import ErrorIterable
from pygoerrors.protocols import Error


def to_errors[T: object, **P](func: Callable[P, T]) -> Callable[P, tuple[T, Error]]:
    """
    Wraps a function to make sure exceptions are returned as errors

    Args:
        func: The function to wrap

    Returns:
        The wrapped function
    """

    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> tuple[T, Error]:
        try:
            return func(*args, **kwargs), Nil
        except Exception as e:
            return cast(T, None), new(str(e))

    return wrapped


def to_errors_iterable[T: object, **P](
    func: Callable[P, Iterable[T]],
) -> Callable[P, ErrorIterable[T]]:
    """
    Wraps a function that returns an iterable into a function that returns an error iterable so that no exceptions are raised

    Args:
        func: The function to wrap

    Returns:
        The wrapped function
    """

    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> ErrorIterable[T]:
        return ErrorIterable(func(*args, **kwargs))

    return wrapped


def cache_ok[T: object, **P](
    cache: MutableMapping[Any, Any] = {},
) -> Callable[[Callable[P, tuple[T, Error]]], Callable[P, tuple[T, Error]]]:
    """
    Cache the result of a function if the result is not an error.

    Args:
        cache: The type of the cache. Can be used with `cachetools.{cache_type}`.

    Returns:
        Wrapped function
    """

    def decorator(
        func: Callable[P, tuple[T, Error]],
    ) -> Callable[P, tuple[T, Error]]:
        cached = cachetools.cached(cache=cache, info=True)(func)

        @functools.wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> tuple[T, Error]:
            result, err = cached(*args, **kwargs)
            if err:
                cached.cache.pop(cached.cache_key(*args, **kwargs))  # type: ignore # pyright: ignore[reportFunctionMemberAccess, reportAny]
                return result, err
            return result, err

        return wrapped

    return decorator
