# Built-in Modules
import abc
import typing
import datetime as dt
from dataclasses import dataclass


# Local Modules
from quantsapp import exceptions as generic_exceptions
from quantsapp._execution import _enums as execution_enums

# ----------------------------------------------------------------------------------------------------

_market_timings_data: dict[execution_enums.Exchange, typing.Any] = {}

# ----------------------------------------------------------------------------------------------------

class _MarketTimings(abc.ABC):

    def __init__(
            self,
            dt_open: dt.datetime = None, # type: ignore
            dt_close: dt.datetime = None, # type: ignore
            is_open_today: bool = False,
    ) -> None:
        self._dt_open = dt_open
        self._dt_close = dt_close
        self._is_open_today = is_open_today
    # TODO add auto reload market timings data every 'n' minutes

    # ---------------------------------------------------------------------------

    @property
    def dt_open(self) -> dt.datetime:
        return self._dt_open

    # ---------------------------------------------------------------------------

    @property
    def dt_close(self) -> dt.datetime:
        return self._dt_close

    # ---------------------------------------------------------------------------

    @property
    def is_open_today(self) -> bool:
        return self._is_open_today

    # ---------------------------------------------------------------------------

    def is_market_open(self) -> bool:
        """Return current status whether market open at time of func invoke"""

        if not self.is_open_today:
            return False

        if not self.dt_open \
                or not self.dt_close:
            raise generic_exceptions.LoginNotInitiatedError('Initiate Login to check Market timings')  # TODO change the exception and its error

        return self.dt_open <= dt.datetime.now(dt.UTC) <= self.dt_close

    # ---------------------------------------------------------------------------

    def is_after_market(self) -> bool:
        """Return current status whether market open at time of func invoke"""

        if not self.is_open_today:
            return True

        if not self.dt_open \
                or not self.dt_close:
            raise generic_exceptions.LoginNotInitiatedError('Initiate Login to check Market timings')  # TODO change the exception and its error

        return dt.datetime.now(dt.UTC) > self.dt_close

    # ---------------------------------------------------------------------------

    def is_within_market_buffer(
            self,
            start_buffer: typing.Optional[dt.timedelta] = None,
            end_buffer: typing.Optional[dt.timedelta] = None,
            dt_time: dt.datetime = dt.datetime.now(dt.UTC),
        ) -> bool:
        """Check if the requested time is within before market open buffer"""

        if not self.is_open_today:
            return False

        _dt_open = self.dt_open
        if start_buffer:
            _dt_open -= start_buffer

        _dt_close = self.dt_close
        if end_buffer:
            _dt_close += end_buffer

        return _dt_open <= dt_time <= _dt_close


# ----------------------------------------------------------------------------------------------------

@dataclass
class MarketTimings(_MarketTimings):  # TODO handle this inheritance in a proper way later

    exchange: execution_enums.Exchange

    # ---------------------------------------------------------------------------

    def __post_init__(self) -> None:

        if self.exchange not in _market_timings_data:
            raise generic_exceptions.InvalidInputError('Invalid Exchange')

        super().__init__(**_market_timings_data[self.exchange])