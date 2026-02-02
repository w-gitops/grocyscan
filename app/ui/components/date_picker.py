"""Touch-friendly date picker component."""

from datetime import date, timedelta
from typing import Callable

from nicegui import ui


class TouchDatePicker:
    """Touch-friendly date picker with quick-select buttons.

    Provides large touch targets (48x48px minimum) and
    quick-select options for common expiration dates.
    """

    # Quick-select options: (label, days_from_now or None for no date)
    QUICK_OPTIONS = [
        ("TODAY", 0),
        ("+3D", 3),
        ("+1W", 7),
        ("+2W", 14),
        ("+1M", 30),
        ("+3M", 90),
        ("NONE", None),
    ]

    def __init__(
        self,
        on_change: Callable[[date | None], None] | None = None,
        initial_value: date | None = None,
        label: str = "Best Before",
    ) -> None:
        """Initialize the date picker.

        Args:
            on_change: Callback when date changes
            initial_value: Initial date value
            label: Label for the date picker
        """
        self.on_change = on_change
        self._value = initial_value
        self._label = label
        self._date_label: ui.label | None = None
        self._buttons: list[ui.button] = []

    @property
    def value(self) -> date | None:
        """Get the current date value."""
        return self._value

    @value.setter
    def value(self, new_value: date | None) -> None:
        """Set the date value."""
        self._value = new_value
        self._update_display()
        if self.on_change:
            self.on_change(new_value)

    def render(self) -> None:
        """Render the date picker component."""
        with ui.column().classes("w-full gap-2"):
            ui.label(self._label).classes("font-semibold")

            # Current date display
            with ui.row().classes("w-full items-center gap-2"):
                ui.icon("event", color="primary")
                self._date_label = ui.label(self._format_date()).classes("text-lg")

            # Quick-select buttons
            ui.label("Quick Select").classes("text-sm text-gray-500 mt-2")

            with ui.row().classes("w-full flex-wrap gap-2"):
                for label, days in self.QUICK_OPTIONS:
                    btn = ui.button(
                        label,
                        on_click=lambda d=days: self._set_quick_date(d),
                    ).classes("min-w-[48px] min-h-[48px]")

                    # Highlight if this matches current selection
                    if self._matches_quick_option(days):
                        btn.props("color=primary")
                    else:
                        btn.props("outline")

                    self._buttons.append(btn)

            # Calendar picker
            with ui.expansion("Choose specific date", icon="calendar_month").classes("w-full mt-2"):
                ui.date(
                    value=self._value.isoformat() if self._value else None,
                    on_change=self._handle_calendar_change,
                ).classes("w-full")

    def _set_quick_date(self, days: int | None) -> None:
        """Set date from quick-select button.

        Args:
            days: Days from today, or None for no date
        """
        if days is None:
            self.value = None
        else:
            self.value = date.today() + timedelta(days=days)

    def _handle_calendar_change(self, e: dict) -> None:
        """Handle calendar date selection."""
        if e.value:
            self.value = date.fromisoformat(e.value)
        else:
            self.value = None

    def _format_date(self) -> str:
        """Format the current date for display."""
        if self._value is None:
            return "No expiration date"

        days_until = (self._value - date.today()).days

        if days_until == 0:
            return f"{self._value.strftime('%Y-%m-%d')} (Today)"
        elif days_until == 1:
            return f"{self._value.strftime('%Y-%m-%d')} (Tomorrow)"
        elif days_until < 0:
            return f"{self._value.strftime('%Y-%m-%d')} ({abs(days_until)} days ago)"
        elif days_until < 7:
            return f"{self._value.strftime('%Y-%m-%d')} ({days_until} days)"
        elif days_until < 30:
            weeks = days_until // 7
            return f"{self._value.strftime('%Y-%m-%d')} ({weeks} week{'s' if weeks > 1 else ''})"
        else:
            months = days_until // 30
            return f"{self._value.strftime('%Y-%m-%d')} ({months} month{'s' if months > 1 else ''})"

    def _matches_quick_option(self, days: int | None) -> bool:
        """Check if current value matches a quick option."""
        if days is None:
            return self._value is None
        if self._value is None:
            return False
        expected = date.today() + timedelta(days=days)
        return self._value == expected

    def _update_display(self) -> None:
        """Update the display after value change."""
        if self._date_label:
            self._date_label.text = self._format_date()

        # Update button highlighting
        for i, (_, days) in enumerate(self.QUICK_OPTIONS):
            if i < len(self._buttons):
                if self._matches_quick_option(days):
                    self._buttons[i].props("color=primary")
                else:
                    self._buttons[i].props("outline")
