from datetime import date, datetime, timedelta, timezone

APP_TIMEZONE = timezone(timedelta(hours=-3))


def today_app() -> date:
    return datetime.now(APP_TIMEZONE).date()
