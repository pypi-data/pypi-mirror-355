from os import getenv


def get_default_constants():
    if getenv("BEAR_IS_PRESENT"):
        from .date_related import DT_FORMAT_WITH_TZ as DEFAULT_DATE_FORMAT
        from .date_related import PT_TIME_ZONE as DEFAULT_TIMEZONE
        from .date_related import TIME_FORMAT as DEFAULT_TIME_FORMAT
