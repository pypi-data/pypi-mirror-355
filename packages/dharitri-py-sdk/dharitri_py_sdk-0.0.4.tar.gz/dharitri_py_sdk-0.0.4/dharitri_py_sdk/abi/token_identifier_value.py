from typing import Any

from dharitri_py_sdk.abi.string_value import StringValue


class TokenIdentifierValue(StringValue):
    def __init__(self, value: str = "") -> None:
        self.value = value

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, TokenIdentifierValue) and self.value == other.value
