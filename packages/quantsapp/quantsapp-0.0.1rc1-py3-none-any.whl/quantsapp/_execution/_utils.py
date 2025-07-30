# Built-in Modules
import typing
import datetime as dt


# Local Modules
from quantsapp._market_timings import MarketTimings
from quantsapp._execution import _enums as execution_enums


# ----------------------------------------------------------------------------------------------------

# Auto reload, when required
__market_timings: MarketTimings = None  # type: ignore

# ----------------------------------------------------------------------------------------------------

def convert_update_sec_to_datetime(micro_sec_value: int, tz: dt.timezone = dt.UTC) -> dt.datetime:

    return dt.datetime.fromtimestamp(
        timestamp=micro_sec_value/1e6,  # Convert microsecond to second
        tz=tz,
    )

# ----------------------------------------------------------------------------------------------------

def is_valid_cache_file(data: dict[str, typing.Any], buffer_time: dt.timedelta) -> bool:
    """Valid only if the last updated time is greater than or equal to market open timings - buffer time"""

    global __market_timings

    if not __market_timings:
        __market_timings = MarketTimings(exchange=execution_enums.Exchange.NSE_FNO)

    try:
        # If today is not market day, then try to fetch only once in a day
        if not __market_timings.is_open_today:
            # If the last updated time is less than 1 day, then the cache file is a valid one
            if (dt.datetime.now(dt.UTC) - data['_last_updated_on']) <= dt.timedelta(days=1):
                return True
            else:
                return False

        # If market day and last updated time within market buffer, then its a valid one
        if __market_timings.is_within_market_buffer(
            start_buffer=buffer_time,
            dt_time=data['_last_updated_on'],
        ):
            return True

        # If the orders synced after market close, then also a valid one
        if data['_last_updated_on'] > __market_timings.dt_close:
            return True

    except Exception:
        return False

    return False