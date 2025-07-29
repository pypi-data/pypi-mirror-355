"""Group for checking integer fields.

Supported fields:
    IntegerField | FloatField
"""

from typing import Any

from ... import translations


class NumGroupMixin:
    """Group for checking integer fields.

    Supported fields:
        IntegerField | FloatField
    """

    async def num_group(self, params: dict[str, Any]) -> None:
        """Checking number fields."""
        field = params["field_data"]
        # Get current value.
        value = field.value
        if value is None:
            value = field.default

        if "Float" in field.field_type:
            if not isinstance(value, (float, type(None))):
                self.panic_type_error("float", params)  # type: ignore[attr-defined]
        else:
            if not isinstance(value, (int, type(None))):
                self.panic_type_error("int", params)  # type: ignore[attr-defined]

        if value is None:
            if field.required:
                err_msg = translations._("Required field !")
                self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
            if params["is_save"]:
                params["result_map"][field.name] = None
            return
        # Validation the `max_number` field attribute.
        max_number = field.max_number
        if max_number is not None and value > max_number:
            err_msg = translations._(
                "The value %d must not be greater than max=%d !" % value, max_number
            )
            self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
        # Validation the `min_number` field attribute.
        min_number = field.min_number
        if min_number is not None and value < min_number:
            err_msg = translations._(
                "The value %d must not be less than min=%d !" % value, min_number
            )
            self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
        # Validation the `unique` field attribute.
        if field.unique and not await self.check_uniqueness(value, params):  # type: ignore[attr-defined]
            err_msg = translations._("Is not unique !")
            self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
        # Insert result.
        if params["is_save"]:
            params["result_map"][field.name] = value
