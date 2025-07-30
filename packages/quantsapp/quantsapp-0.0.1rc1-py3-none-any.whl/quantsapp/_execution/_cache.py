# Local Modules
from quantsapp._execution._modules._broker_list_models import ResponseListMappedBrokers_Type
from quantsapp._execution._modules._order_list_models import CacheOrderListingData_Type
from quantsapp._execution._modules._position_list_models import (
    CachePositionsCombinedData_Type,
    CachePositionsAccountwiseData_Type,
)

# ----------------------------------------------------------------------------------------------------

mapped_brokers: ResponseListMappedBrokers_Type = None  # type: ignore

orders: CacheOrderListingData_Type = {
    'data': {},
}  # type: ignore
positions: CachePositionsAccountwiseData_Type = {
    'data': {},
}  # type: ignore
positions_combined: CachePositionsCombinedData_Type = {
    'data': [],
}  # type: ignore