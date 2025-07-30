import sys

if sys.version_info < (3, 11):
    from bear_epoch_time._time_class_legacy import EpochTimestamp
else:
    from bear_epoch_time._time_class import EpochTimestamp

from bear_epoch_time._helpers import convert_to_seconds, seconds_to_time
from bear_epoch_time.constants.date_related import DT_FORMAT_WITH_TZ_AND_SECONDS
from bear_epoch_time.constants.time_related import SECONDS_IN_MINUTE, SECONDS_IN_MONTH


def test_month_and_minute_parsing():
    total: int = convert_to_seconds("1M 5m")
    assert total == SECONDS_IN_MONTH + 5 * SECONDS_IN_MINUTE


def test_seconds_to_time_month_format():
    assert seconds_to_time(SECONDS_IN_MONTH) == "1M"


def test_epoch_timestamp():
    EpochTimestamp.set_full_format(DT_FORMAT_WITH_TZ_AND_SECONDS)
    timestamp = EpochTimestamp(value=1749777032000)  # 06-12-2025 06:10:32 PM PDT
    formatted: str = timestamp.to_string()
    assert formatted == "06-12-2025 06:10:32 PM PDT", f"Expected '06-12-2025 06:10:32 PM PDT', got '{formatted}'"
