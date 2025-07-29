from .decorators import cache_ok, to_errors, to_errors_iterable
from .errors import as_, is_, join, new
from .format import errorf
from .helpers import Nil, NotSet
from .protocols import Error, Result

__all__ = [
    # types
    "Error",
    "Nil",
    "NotSet",
    "Result",
    # core
    "new",
    "is_",
    "as_",
    "join",
    "errorf",
    # decorators
    "to_errors",
    "to_errors_iterable",
    "cache_ok",
]
