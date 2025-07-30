# Built-in Modules
import typing
import datetime as dt


BROKER_LISTING_DATETIME_FORMAT: str = '%d-%b-%y %H:%M:%S'

BROKER_ORDER_PLACEMENT_DATE_FORMAT: str = '%d-%b-%y'

DEFAULT_LIST_AVAILABLE_BROKER_NAME_TYPE: typing.Literal['enum'] = 'enum'


ORDER_LISTING_VALID_CACHE_FILE_MARKET_BUFFER: dt.timedelta = dt.timedelta(minutes=15)
POSITION_LISTING_VALID_CACHE_FILE_MARKET_BUFFER: dt.timedelta = dt.timedelta(minutes=15)
POSITION_COMBINED_LISTING_VALID_CACHE_FILE_MARKET_BUFFER: dt.timedelta = dt.timedelta(minutes=15)