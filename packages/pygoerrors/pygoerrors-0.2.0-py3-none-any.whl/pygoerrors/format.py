from pygoerrors.errors import stringError, wrappedError
from pygoerrors.protocols import Error


def errorf(format_str: str, *args: object) -> Error:
    """
    Format a string and an error. Use `%w` to wrap an error

    Args:
        format_str: The string to format
        args: The arguments to format

    Returns:
        A new error with the formatted string and wrapped error.

    Raises:
        ValueError: When no argument is provided for `%w`
        TypeError: When the argument for `%w` doesn't implement the Error protocol
    """
    if "%w" in format_str:
        if format_str.count("%w") != 1:
            raise ValueError("Only one '%w' verb is allowed in format string")

        idx = format_str.index("%w")
        before = format_str[:idx]
        after = format_str[idx + 2 :]

        if not args:
            raise ValueError("No arguments provided for '%w'")

        *fmt_args, err = args
        if not isinstance(err, Error):
            raise TypeError("The argument for '%w' must implement the Error protocol")
        fmt = before + err.error() + after

        return wrappedError(fmt % fmt_args, err)
    else:
        message = format_str % args
        return stringError(message)
