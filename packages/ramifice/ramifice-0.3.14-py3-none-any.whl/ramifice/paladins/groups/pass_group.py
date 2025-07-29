"""Group for checking password fields.

Supported fields: PasswordField
"""

from typing import Any

from argon2 import PasswordHasher

from ... import translations


class PassGroupMixin:
    """Group for checking password fields.

    Supported fields: PasswordField
    """

    def pass_group(self, params: dict[str, Any]) -> None:
        """Checking password fields."""
        field = params["field_data"]
        # When updating the document, skip the verification.
        if params["is_update"]:
            params["field_data"].value = None
            return
        # Get current value.
        value = field.value or None

        if not isinstance(value, (str, type(None))):
            self.panic_type_error("str", params)  # type: ignore[attr-defined]

        if value is None:
            if field.required:
                err_msg = translations._("Required field !")
                self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
            if params["is_save"]:
                params["result_map"][field.name] = None
            return
        # Validation Passwor.
        if not field.is_valid(value):
            err_msg = translations._("Invalid Password !")
            self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
            chars = "a-z A-Z 0-9 - . _ ! \" ` ' # % & , : ; < > = @ { } ~ $ ( ) * + / \\ ? [ ] ^ |"
            err_msg = translations._("Valid characters: %s" % chars)
            self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
            err_msg = translations._("Number of characters: from 8 to 256")
            self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
        # Insert result.
        if params["is_save"]:
            ph = PasswordHasher()
            hash: str = ph.hash(value)
            params["result_map"][field.name] = hash
