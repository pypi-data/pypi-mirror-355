"""Field of Model for enter password."""

import json
from typing import Any

from ..store import REGEX
from .general.field import Field


class PasswordField(Field):
    r"""Field of Model for enter password.

    Warning:
            Regular expression: ^[-._!"`'#%&,:;<>=@{}~$()*+/\\?[]^|a-zA-Z0-9]{8,256}$
            Valid characters: a-z A-Z 0-9 - . _ ! " ` ' # % & , : ; < > = @ { } ~ $ ( ) * + / \\ ? [ ] ^ |
            Number of characters: from 8 to 256.
    """

    def __init__(  # noqa: D107
        self,
        label: str = "",
        hide: bool = False,
        ignored: bool = False,
        hint: str = "",
        warning: list[str] | None = None,
        placeholder: str = "",
        required: bool = False,
    ):
        Field.__init__(
            self,
            label=label,
            disabled=False,
            hide=hide,
            ignored=ignored,
            hint=hint,
            warning=warning,
            field_type="PasswordField",
            group="pass",
        )

        self.input_type = "password"
        self.value: str | None = None
        self.placeholder = placeholder
        self.required = required

    def is_valid(self, value: str | None = None) -> bool:
        """Validate Password."""
        flag = True
        password = str(value or self.value)
        if not REGEX["password"].match(password):
            flag = False
        return flag

    def to_dict(self) -> dict[str, Any]:
        """Convert object instance to a dictionary."""
        json_dict: dict[str, Any] = {}
        for name, data in self.__dict__.items():
            if not callable(data):
                json_dict[name] = data if name != "value" else None
        return json_dict

    def to_json(self) -> str:
        """Convert object instance to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Any:
        """Convert JSON string to a object instance."""
        obj = cls()
        for name, data in json_dict.items():
            obj.__dict__[name] = data
        return obj

    @classmethod
    def from_json(cls, json_str: str) -> Any:
        """Convert JSON string to a object instance."""
        json_dict = json.loads(json_str)
        return cls.from_dict(json_dict)
