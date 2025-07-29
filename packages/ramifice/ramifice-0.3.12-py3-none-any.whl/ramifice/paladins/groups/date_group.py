"""Group for checking date fields.

Supported fields:
    DateTimeField | DateField
"""

from typing import Any

from babel.dates import format_date, format_datetime

from ... import translations


class DateGroupMixin:
    """Group for checking date fields.

    Supported fields:
        DateTimeField | DateField
    """

    def date_group(self, params: dict[str, Any]) -> None:
        """Checking date fields."""
        field = params["field_data"]
        # Get current value.
        value = field.value or field.default or None
        if value is None:
            if field.required:
                err_msg = translations._("Required field !")
                self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
            if params["is_save"]:
                params["result_map"][field.name] = None
            return
        #
        # Validation the `max_date` field attribute.
        max_date = field.max_date
        if max_date is not None and value > max_date:
            value_str = (
                format_date(
                    date=value.date(),
                    format="short",
                    locale=translations.CURRENT_LOCALE,
                )
                if field.field_type == "DateField"
                else format_datetime(
                    datetime=value,
                    format="short",
                    locale=translations.CURRENT_LOCALE,
                )
            )
            max_date_str = (
                format_date(
                    date=max_date.date(),
                    format="short",
                    locale=translations.CURRENT_LOCALE,
                )
                if field.field_type == "DateField"
                else format_datetime(
                    datetime=max_date,
                    format="short",
                    locale=translations.CURRENT_LOCALE,
                )
            )
            err_msg = translations._(
                "The date %s must not be greater than max=%s !" % value_str,
                max_date_str,
            )
            self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
        # Validation the `min_date` field attribute.
        min_date = field.min_date
        if min_date is not None and value < min_date:
            value_str = (
                format_date(
                    date=value.date(),
                    format="short",
                    locale=translations.CURRENT_LOCALE,
                )
                if field.field_type == "DateField"
                else format_datetime(
                    datetime=value,
                    format="short",
                    locale=translations.CURRENT_LOCALE,
                )
            )
            min_date_str = (
                format_date(
                    date=min_date.date(),
                    format="short",
                    locale=translations.CURRENT_LOCALE,
                )
                if field.field_type == "DateField"
                else format_datetime(
                    datetime=min_date,
                    format="short",
                    locale=translations.CURRENT_LOCALE,
                )
            )
            err_msg = translations._(
                "The date %s must not be less than min=%s !" % value_str, min_date_str
            )
            self.accumulate_error(err_msg, params)  # type: ignore[attr-defined]
        # Insert result.
        if params["is_save"]:
            params["result_map"][field.name] = value
