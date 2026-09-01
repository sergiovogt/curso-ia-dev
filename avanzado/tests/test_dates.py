from datetime import date, datetime, timezone
from unittest.mock import patch

from app.dates import APP_TIMEZONE, today_app


def test_today_app_early_utc_returns_previous_day_in_utc_minus_3():
    fixed_utc = datetime(2026, 7, 3, 2, 0, tzinfo=timezone.utc)

    with patch("app.dates.datetime") as mock_datetime:
        mock_datetime.now.side_effect = lambda tz=None: fixed_utc.astimezone(tz or APP_TIMEZONE)
        assert today_app() == date(2026, 7, 2)


def test_today_app_later_utc_returns_same_calendar_day_in_utc_minus_3():
    fixed_utc = datetime(2026, 7, 3, 15, 0, tzinfo=timezone.utc)

    with patch("app.dates.datetime") as mock_datetime:
        mock_datetime.now.side_effect = lambda tz=None: fixed_utc.astimezone(tz or APP_TIMEZONE)
        assert today_app() == date(2026, 7, 3)
