"""Field of Model for enter phone number."""

import phonenumbers

from ..mixins import JsonMixin
from ..store import DEBUG
from .general.field import Field
from .general.text_group import TextGroup


class PhoneField(Field, TextGroup, JsonMixin):
    """Field of Model for enter phone number.

    WARNING: By default is used validator `phonenumbers.is_valid_number()`.
    """

    def __init__(  # noqa: D107
        self,
        label: str = "",
        disabled: bool = False,
        hide: bool = False,
        ignored: bool = False,
        hint: str = "",
        warning: list[str] | None = None,
        default: str | None = None,
        placeholder: str = "",
        required: bool = False,
        readonly: bool = False,
        unique: bool = False,
    ):
        if DEBUG:
            if default is not None:
                if not isinstance(default, str):
                    raise AssertionError("Parameter `default` - Not а `str` type!")
                if len(default) == 0:
                    raise AssertionError(
                        "The `default` parameter should not contain an empty string!"
                    )
                try:
                    phone_default = phonenumbers.parse(default)
                    if not phonenumbers.is_valid_number(phone_default):
                        raise AssertionError()
                except phonenumbers.phonenumberutil.NumberParseException:
                    raise AssertionError("Parameter `default` - Invalid Phone number!")

        Field.__init__(
            self,
            label=label,
            disabled=disabled,
            hide=hide,
            ignored=ignored,
            hint=hint,
            warning=warning,
            field_type="PhoneField",
            group="text",
        )
        TextGroup.__init__(
            self,
            input_type="tel",
            placeholder=placeholder,
            required=required,
            readonly=readonly,
            unique=unique,
        )
        JsonMixin.__init__(self)

        self.default = default

    def is_valid(self, value: str | None = None) -> bool:
        """Validate Phone number."""
        flag = True
        number = str(value or self.value or self.default)
        try:
            phone = phonenumbers.parse(number)
            if not phonenumbers.is_valid_number(phone):
                flag = False
        except phonenumbers.phonenumberutil.NumberParseException:
            flag = False
        return flag
