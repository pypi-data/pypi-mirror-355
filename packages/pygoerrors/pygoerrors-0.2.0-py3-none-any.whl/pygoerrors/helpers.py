from typing import override

from pygoerrors.protocols import Error


class NilType(Error):
    @override
    def __repr__(self) -> str:
        return "Nil"

    def __bool__(self) -> bool:
        return False

    @override
    def __eq__(self, value: object, /) -> bool:
        if isinstance(value, NilType):
            return True

        return value is None

    @override
    def error(self) -> str:
        return ""


# Deprecated: Use Nil instead
NotSet = NilType()

# Type to use when an Error is not set
Nil = NilType()
