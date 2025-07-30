__version__ = "1.0.3"

import sys

if sys.version_info < (3, 11):
    from ._time_class_legacy import EpochTimestamp
else:
    from ._time_class import EpochTimestamp

from ._timer import TimerData, create_timer, timer
from ._tools import add_ord_suffix
from .constants.date_related import DATE_FORMAT, DATE_TIME_FORMAT
from .time_manager import TimeTools

__all__ = [
    "EpochTimestamp",
    "TimerData",
    "create_timer",
    "timer",
    "TimeTools",
    "add_ord_suffix",
    "DATE_FORMAT",
    "DATE_TIME_FORMAT",
    "__version__",
]
