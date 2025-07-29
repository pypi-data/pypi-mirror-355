# pygoerrors

A Python library that brings Go-style error handling to Python, enabling error values, wrapping, and inspection without relying on exceptions.​

## 🚀 Features

- Error Values: Return errors as values instead of raising exceptions.
- Error Wrapping: Wrap errors with contextual messages, similar to Go's fmt.Errorf("...: %w", err).
- Error Inspection: Traverse error chains using unwrap(), is\_(), and as\_().
- Protocol-Based Design: Utilize Python's Protocol to define error interfaces.
- No Exceptions: Emphasize functional programming by avoiding exceptions entirely.​

## 📦 Installation

Install the package using pip:

```sh
pip install pygoerrors
```

## 🧑‍💻 Usage

### Defining Custom Errors

```python
import pygoerrors

MyOtherError = pygoerrors.new("some error")

class MyErrorClass(pygoerrors.Error):
    def error(self) -> str:
        return "some error"
```

### Wrapping Errors

```python
import pygoerrors

class MyErrorClass(pygoerrors.Error):
    def error(self) -> str:
        return "base error"

base_err = MyErrorClass()
assert base_err.error() == "base error"

wrapped_err = pygoerrors.errorf("wrapped: %w", base_err)
assert wrapped_err.error() == "wrapped: base error"
```

### Inspecting Errors

```python
import pygoerrors

class MyErrorClass(pygoerrors.Error):
    def error(self) -> str:
        return "base error"

base_err = MyErrorClass()
assert base_err.error() == "base error"

wrapped_err = pygoerrors.errorf("wrapped: %w", base_err)
assert wrapped_err.error() == "wrapped: base error"

assert pygoerrors.is_(wrapped_err, MyErrorClass())

instance = pygoerrors.as_(err, MyErrorClass)
assert instance.error() == "base error"
```
