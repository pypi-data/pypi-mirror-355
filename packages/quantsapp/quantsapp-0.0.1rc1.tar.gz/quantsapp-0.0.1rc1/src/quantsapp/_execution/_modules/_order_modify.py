# Built-in Modules
import time
import typing

from dataclasses import dataclass


# Local Modules
from quantsapp._master_data import MasterData
from quantsapp._market_timings import MarketTimings
from quantsapp import (
    exceptions as generic_exceptions,
    _models as generic_models,
)
from quantsapp._websocket._options_main_ws import OptionsMainWebsocket
from quantsapp._websocket import (
    _config as websocket_config,
)
from quantsapp._execution import (
    _cache as execution_cache,
    _enums as execution_enums,
)

from quantsapp._execution._modules._order_modify_models import (
    ApiResponseModifyOrder_Type,
    PayloadModifyOrder_Pydantic,
)

# from quantsapp._execution._modules._order_list import GetOrders
from quantsapp._execution._modules._order_list_models import (
    ResponseOrderListingData_Type,
    # PayloadListOrders_Pydantic,
)



# ----------------------------------------------------------------------------------------------------


@dataclass
class ModifyOrder:

    ws: OptionsMainWebsocket
    order: PayloadModifyOrder_Pydantic

    # ---------------------------------------------------------------------------

    def modify_order(self) -> str:
        """Modify the existing order"""

        self._validate_data()

        _modify_payload = { # type: ignore
            'action': websocket_config.WsActionKeys.BROKER_ORDERS,
            'mode': 'modify_order',
            'broker_client': self.order.broker_client._api_str,  # type: ignore - private variable
            'b_orderid': self.order.b_orderid,
            'e_orderid': self.order.e_orderid,
            'order': {
                'qty': self.order.qty,
                'price': self.order.price
            }
        }

        if self.order.stop_price:
            _modify_payload['order']['stop_price'] = self.order.stop_price

        modify_order_resp: ApiResponseModifyOrder_Type = self.ws.invoke_api(
            # TODO try to make this more generic and take it from some config
            payload=_modify_payload, # type: ignore
        ) # type: ignore

        if modify_order_resp['status'] != '1':
            raise generic_exceptions.BrokerOrdersPlacingFailed(modify_order_resp['msg'])

        # Wait for sometime, so that the order update will be recevied and update the modification on cache data
        # TODO check whether order update websocket is connected or not
        time.sleep(1)

        return 'Order Modified'

    # ---------------------------------------------------------------------------

    def _validate_data(self) -> None:
        """validate the data which can't be done from the pydantic level(may be due to circular import Error)"""

        if not MarketTimings(exchange=execution_enums.Exchange.NSE_FNO).is_market_open():
            raise generic_exceptions.InvalidInputError('Market Closed')

        if exist_order := self._get_existing_order():
            self._validate_order_status(exist_order)
            self._validate_qty(exist_order)

    # ---------------------------------------------------------------------------

    def _validate_order_status(self, exist_order: ResponseOrderListingData_Type) -> None:

        if exist_order['order_status'] in (
            execution_enums.OrderStatus.CANCELLED,
            execution_enums.OrderStatus.COMPLETED,
            execution_enums.OrderStatus.FAILED,
            execution_enums.OrderStatus.REJECTED,
        ):
            raise generic_exceptions.InvalidInputError(f"Order already {exist_order['order_status']}")

    # ---------------------------------------------------------------------------

    def _validate_qty(self, exist_order: ResponseOrderListingData_Type) ->None:

        _tmp_instr = generic_models._Instrument_Pydantic.from_api_str(exist_order['instrument'])

        _lot_size: int = MasterData.master_data['symbol_data'][_tmp_instr.symbol]['lot_size'][_tmp_instr.expiry]

        if self.order.qty % _lot_size != 0:
            raise generic_exceptions.InvalidInputError(f"Invalid Qty, should be multiple of {_lot_size} for {_tmp_instr.symbol!r}")

    # ---------------------------------------------------------------------------

    def _get_existing_order(self) -> typing.Optional[ResponseOrderListingData_Type]:
        """Get the existing order from cache, if not found then try fetching from api again"""

        # TODO move this to generic area where it can be used by other modules

        _tmp_order_id_ref = f"{self.order.b_orderid}|{self.order.e_orderid}"

        if not (_exist_order_data := execution_cache.orders['data'].get(self.order.broker_client, {}).get(_tmp_order_id_ref)) \
                and execution_cache.orders['data']:
            raise generic_exceptions.InvalidInputError('Broker Order Not found')

        return _exist_order_data
