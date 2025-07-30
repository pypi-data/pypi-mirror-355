# Built-in Modules
import enum


# Local Modules
from quantsapp._enum_meta import _QappEnumMeta

@enum.unique
class Exchange(enum.StrEnum, metaclass=_QappEnumMeta):
    """Exchange to be used in the execution module"""

    NSE_FNO = 'NSE-FO'

    def __repr__(self):
        """Representation String"""
        return f"{self.__class__.__name__}.{self.name}"


@enum.unique
class Broker(enum.StrEnum, metaclass=_QappEnumMeta):
    """Broker to be used in the execution module"""

    ALICEBLUE = 'aliceblue'
    ANGEL = 'angel'
    CHOICE = 'choice'
    DHAN = 'dhan'
    FIVEPAISA = 'fivepaisa'
    FIVEPAISA_XTS = 'fivepaisa-xts'
    FYERS = 'fyers'
    MOTILAL_OSWAL = 'mo'
    MSTOCK = 'mstock'
    NUVAMA = 'nuvama'
    SHAREKHAN = 'sharekhan'
    UPSTOX = 'upstox'
    ZERODHA = 'zerodha'

    # TODO move it to metaclass
    def __repr__(self):
        """Representation String"""
        return f"{self.__class__.__name__}.{self.name}"


@enum.unique
class BrokerRole(enum.StrEnum, metaclass=_QappEnumMeta):
    """BrokerRole to be used in the execution module"""

    OWNER = 'owner'
    READER = 'reader'
    EXECUTOR = 'executor'

    def __repr__(self):
        """Representation String"""
        return f"{self.__class__.__name__}.{self.name}"

@enum.unique
class BrokerAccountValidity(enum.StrEnum, metaclass=_QappEnumMeta):
    """Broker Account Validity to be used in the execution module"""

    EXPIRED = '-2'
    UNKNOWN = '-1'
    INFINITY = '0'

    def __repr__(self):
        """Representation String"""
        return f"{self.__class__.__name__}.{self.name}"


@enum.unique
class OrderBuySell(enum.StrEnum, metaclass=_QappEnumMeta):
    """Order Buy Sell to be used in the execution module"""

    BUY = 'b'
    SELL = 's'

    def __repr__(self):
        """Representation String"""
        return f"{self.__class__.__name__}.{self.name}"

@enum.unique
class OrderProductType(enum.StrEnum, metaclass=_QappEnumMeta):
    """Order Product Type to be used in the execution module"""

    INTRADAY = 'intraday'
    NRML = 'nrml'

    def __repr__(self):
        """Representation String"""
        return f"{self.__class__.__name__}.{self.name}"


@enum.unique
class OrderType(enum.StrEnum, metaclass=_QappEnumMeta):
    """Order Type to be used in the execution module"""

    LIMIT = 'limit'
    MARKET = 'market'
    SLL = 'sll'
    SL_M = 'slm'

    def __repr__(self):
        """Representation String"""
        return f"{self.__class__.__name__}.{self.name}"

@enum.unique
class OrderStatus(enum.StrEnum, metaclass=_QappEnumMeta):
    """Order Status to be used in the execution module"""

    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    PARTIAL = 'partial'
    PENDING = 'pending'
    FAILED = 'failed'
    PLACED = 'placed'
    REJECTED = 'rejected'
    TRANSIT = 'transit'

    def __repr__(self):
        """Representation String"""
        return f"{self.__class__.__name__}.{self.name}"


@enum.unique
class OrderValidity(enum.StrEnum, metaclass=_QappEnumMeta):
    """Order Validity to be used in the execution module"""

    DAY = 'day'
    IOC = 'ioc'

    def __repr__(self):
        """Representation String"""
        return f"{self.__class__.__name__}.{self.name}"

