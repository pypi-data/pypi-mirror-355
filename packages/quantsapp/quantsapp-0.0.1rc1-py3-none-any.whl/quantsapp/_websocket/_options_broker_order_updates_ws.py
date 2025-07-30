# Built-in Modules
import json
import time
import gzip
import struct
import typing
import threading
import datetime as dt
import collections.abc


# Third-party Modules
import websocket


# Local Modules
from quantsapp._logger import qapp_logger
from quantsapp._websocket._abstract_ws import QappWebsocket
from quantsapp._market_timings import MarketTimings
from quantsapp._websocket import (
    _models as websocket_models,
    _config as websocket_config,
)

from quantsapp._execution import (
    _utils as execution_utils,
    _cache as execution_cache,
    _enums as execution_enums,
    _models as execution_models,
)

from quantsapp._execution._modules._order_list import GetOrders
from quantsapp._execution._modules._order_list_models import ResponseOrderListingData_Type

from quantsapp import (
    _utils as generic_utils,
    _models as generic_models,
    constants as generic_constants,
)

# ----------------------------------------------------------------------------------------------------


class OptionsBrokerOrderUpdatesWebsocket(QappWebsocket):

    _last_active_at: int = 0

    # ---------------------------------------------------------------------------

    def __init__(
            self,
            url: str,
            ws_conn_cond: threading.Condition,
            order_updates_callback: collections.abc.Callable[[websocket_models.OrderUpdatesWs], typing.Any],
        ) -> None:

        self.ws_conn_cond = ws_conn_cond

        # Create ws connection
        QappWebsocket.__init__(
            self,
            url=url,
            ws_conn_cond=ws_conn_cond,
            thread_name=self.__class__.__name__,

            # Wait till the condition met and then connect to ws
            wait_condition={
                'wait_condition': OptionsBrokerOrderUpdatesWebsocket.should_wait_to_connect_broker_order_updates_ws,
                'notify_condition': self._notify_ws_cond,
                'sleep_sec': websocket_config.SLEEP_TIME_BROKER_ORDER_UPDATE_WS_CONNECTION_CHECK,
            }
        )

        self.order_updates_callback = order_updates_callback

        # For the api invocation usages
        self._responses: dict[str, typing.Any] = {}

        # Storing Websocket Session data
        self.ws_session_data = None

    # ---------------------------------------------------------------------------

    def on_reconnect(self, ws: websocket.WebSocket) -> None:
        qapp_logger.debug(f"AutoReconnect {self.__class__.__name__} -> {ws = }")

    # ---------------------------------------------------------------------------

    def on_message(self, ws: websocket.WebSocket, message: bytes | str) -> None:

        if isinstance(message, bytes):
            """sample message
            b"\x0e\x00\x05\x01\x00\x00choice,X253314\x1f\x8b\x08\x00K\x8eJh\x02\xffUPMK\x031\x10\xfd+%\xe7V\xf2\xb9!K/^\x04=(B\x05=\x85m6\xc5\xc0~5\x99\x1c\x8a\xf8\xdf\xcdd\xa9\xd6\x9c\xde\xcc{\xf3\xe6M\xbeH\xe7H\xbb!\xees\x0e\xceo\xdf\xb9\x12\x82I\xb2\xdd\x90\xa3\x9dc\xefc\xe8\x91\xbe?\xbc\xbe\xbc\xd1\xf2\xd8\xbeA\xd2\xdf\x92L\xd2J\t\xddHe\xb8F\xc1\xd9F\x7f\xb2\x95gX\xc2\xc5\x9e\xc20xl\xd0\xb5Q\x90V\x05\x86)A\xcc\xa3\x9f\x00\xcd\x9e\x1f\x1f\x0e\x1f-\xe3\xbb\xa7<\xed\xb8j]\xcb\x15U\xb4&J(8"\bI\x8bVwL]\xcb\xff\x0b\x8e6\'\xefl^\xfa\x0eP\xc9\xb44\x9a\t\xae\xe9\xfa\xea\xd4\xdcg\x07\x16.\x0b*\xc8\x14\xc7\x01\xcd\xebi6A\x07\xb9n\x84\xd8M)@\xa5\xac\x83Xz\xa2\xe0\xe2\xbf~@\xc3\xb92\xf2w\xf0j7\x84q\x1d:\xd7(7\x19\x84\xd4\xdc\x18\xc3\x0b\x97`^\xec\xdf5\xf4\xfb\x07\xff\xf2\xc6\xbe\x91\x01\x00\x00"
            """

            len_broker_client, _len_data = struct.unpack('<hi', message[0:6])

            _order_update: websocket_models.BrokerOrderUpdateRawWsData_Type = json.loads(gzip.decompress(message[6+len_broker_client:]))

            # qapp_logger.debug(f"Received on ws -> {_order_update = }")

            _parsed_order = self._process_broker_order_update(_order_update)

            self.order_updates_callback(_parsed_order)

        elif isinstance(message, str):
            _resp = json.loads(message)
            if _resp.get('ws_msg_type') == 'qapp_broker_updates_options_subscription_success':

                """sample _resp
                {
                    "status": "1",
                    "msg": "success",
                    "ws_msg_type": "qapp_broker_updates_options_subscription_success"
                }
                """

                # Notify the other thread that the ws connected successfully 
                self._notify_ws_cond()

                # Set the last active conn status time
                OptionsBrokerOrderUpdatesWebsocket._last_active_at = int(time.time())

                qapp_logger.debug(f"{self.__class__.__name__} connected!!!")

    # ---------------------------------------------------------------------------

    def on_error(self, ws: websocket.WebSocket, error: Exception) -> None:
        qapp_logger.error(f"Error on {self.__class__.__name__}")
        qapp_logger.error(f"{ws = }")
        qapp_logger.error(f"{error = }")

    # ---------------------------------------------------------------------------

    def on_close(self, ws: websocket.WebSocket, close_status_code: int, close_msg: str) -> None:
        qapp_logger.debug(f"{self.__class__.__name__} closed -> {close_status_code = }, {close_msg = }")

    # ---------------------------------------------------------------------------

    def on_pong(self, ws: websocket.WebSocket, message: str) -> None:
        OptionsBrokerOrderUpdatesWebsocket._last_active_at = int(time.time())

    # ---------------------------------------------------------------------------

    def _notify_ws_cond(self) -> None:
        """Notify the websocket condition lock to proceed further"""

        with self.ws_conn_cond:
            self.ws_conn_cond.notify()

    # ---------------------------------------------------------------------------

    def _process_broker_order_update(self, order_data: websocket_models.BrokerOrderUpdateRawWsData_Type) -> websocket_models.OrderUpdatesWs:
        """Parse the real-time broker ws order data to client format"""

        _tmp_broker_client = execution_models.BrokerClient.from_api_str(order_data['ac'])
        _tmp_order_ref_internal_id = f"{order_data['b_orderid']}|{order_data.get('e_orderid', '0')}"
        _tmp_exist_order = execution_cache.orders['data'].setdefault(_tmp_broker_client, {}).get(_tmp_order_ref_internal_id)

        # For some broker, on order placement the exchange order_id is not present or '0', then after it got placed or modified with exchange,
        # they are sending with proper exchange order id, to handle this first check if the give exchange order_id is present or not
        # if not present, then check for 'broker_order_id|0' and remove that entry from cache, since it will be updated with new e_orderid
        if not _tmp_exist_order:
            _tmp_exist_order = execution_cache.orders['data'].setdefault(_tmp_broker_client, {}).pop(f"{order_data['b_orderid']}|0", None)

        if not _tmp_exist_order:
            _tmp_exist_order = next(
                (
                    _broker_client_data
                    for _broker_client_id, _broker_client_data in execution_cache.orders['data'].setdefault(_tmp_broker_client, {}).items()
                    if _broker_client_id.startswith(order_data['b_orderid'])
                ),
                None,  # Default value
            )

        is_modify_local_cache_file_required = False

        _new_order = websocket_models.BrokerOrderUpdateWsData_Pydantic(
            broker_client=_tmp_broker_client,
            b_orderid=order_data['b_orderid'],
            e_orderid=order_data.get('e_orderid', '0'),
            userid=str(order_data['userid']),
            instrument=generic_models._Instrument_Pydantic.from_api_str(order_data['instrument']).api_instr_str,
            buy_sell=execution_enums.OrderBuySell(order_data['bs']),
            product_type=execution_enums.OrderProductType(order_data['product_type']),
            order_status=execution_enums.OrderStatus(order_data['order_status']),
            order_type=execution_enums.OrderType(order_data['order_type']),
            q_ref_id=order_data['q_ref_id'],
            o_ctr=order_data['o_ctr'],
            qty=order_data['qty'],
            qty_filled=order_data['qty_filled'],
            price=order_data['price'],
            price_filled=order_data['price_filled'],
            stop_price=order_data.get('stop_price', 0),
            q_usec=execution_utils.convert_update_sec_to_datetime(order_data['q_usec']),
            b_usec_update=execution_utils.convert_update_sec_to_datetime(order_data['b_usec_update']),
        )

        # The order received is not in the cache data
        if not _tmp_exist_order:
            _tmp_new_order: ResponseOrderListingData_Type = {
                'broker_client': _tmp_broker_client,
                'b_orderid': _new_order.b_orderid,
                'e_orderid': _new_order.e_orderid,
                'userid': _new_order.userid,
                'instrument': _new_order.instrument,
                'buy_sell': _new_order.buy_sell,
                'product_type': _new_order.product_type,
                'order_status': _new_order.order_status,
                'order_type': _new_order.order_type,
                'q_ref_id': _new_order.q_ref_id,
                'o_ctr': _new_order.o_ctr,
                'qty': _new_order.qty,
                'qty_filled': _new_order.qty_filled,
                'price': _new_order.price,
                'price_filled': _new_order.price_filled,
                'stop_price': _new_order.stop_price,
                'q_usec': _new_order.q_usec,
                'b_usec_update': _new_order.b_usec_update,
            }
            execution_cache.orders['data'][_tmp_broker_client][_tmp_order_ref_internal_id] = _tmp_new_order

            qapp_logger.debug(f"Realtime Order (new) updated to cache order -> {_tmp_new_order}")

            is_modify_local_cache_file_required = True


        # if the order exists and only if the 'o_ctr' counter is more than the previous one
        elif order_data.get('o_ctr', 0) >= _tmp_exist_order['o_ctr']:

            # TODO change the temp exist order dict to pydantic model (if required)
            # TODO avoid creating pydantic model as above for only updating below details

            is_e_orderid_modified = bool(_tmp_exist_order['e_orderid'] != _new_order.e_orderid)

            # Sometimes the order updates coming with e_orderid as '0' after receving a proper exchange id
            # To handle this case, consider updating e_orderid only when changed and not equal to '0'
            if (_tmp_exist_order['e_orderid'] != _new_order.e_orderid) \
                    and (_new_order.e_orderid != '0'):
                _tmp_exist_order['e_orderid'] = _new_order.e_orderid

            _tmp_exist_order['userid'] = _new_order.userid
            _tmp_exist_order['q_ref_id'] = _new_order.q_ref_id
            _tmp_exist_order['qty'] = _new_order.qty
            _tmp_exist_order['qty_filled'] = _new_order.qty_filled
            _tmp_exist_order['price'] = _new_order.price
            _tmp_exist_order['price_filled'] = _new_order.price_filled
            _tmp_exist_order['b_usec_update'] = _new_order.b_usec_update
            _tmp_exist_order['product_type'] = _new_order.product_type
            _tmp_exist_order['order_status'] = _new_order.order_status
            _tmp_exist_order['o_ctr'] = _new_order.o_ctr
            _tmp_exist_order['order_type'] = _new_order.order_type
            _tmp_exist_order['q_usec'] = _new_order.q_usec
            _tmp_exist_order['stop_price'] = _new_order.stop_price

            if is_e_orderid_modified:
                execution_cache.orders['data'][_tmp_broker_client][_tmp_order_ref_internal_id] = _tmp_exist_order

            qapp_logger.debug(f"Realtime Order (old) updated to cache order -> {_tmp_exist_order}")

            is_modify_local_cache_file_required = True


        if is_modify_local_cache_file_required:
            execution_cache.orders['_last_updated_on'] = dt.datetime.now(tz=generic_constants.DT_ZONE_IST)
            GetOrders.save_cache_data(data=execution_cache.orders)

        return _new_order.model_dump()

    # ---------------------------------------------------------------------------

    @staticmethod
    def should_connect_broker_order_updates_ws() -> bool:

        _market_timings = MarketTimings(exchange=execution_enums.Exchange.NSE_FNO)

        # Non-trading day - Don't Allow
        if not _market_timings.is_open_today:
            return False

        # If after market timings - Don't Allow
        if _market_timings.is_after_market():
            return False

        return True

    # ---------------------------------------------------------------------------

    @staticmethod
    def should_wait_to_connect_broker_order_updates_ws() -> bool:

        return not MarketTimings(exchange=execution_enums.Exchange.NSE_FNO).is_within_market_buffer(
            start_buffer=websocket_config.ALLOW_BROKER_ORDER_WS_CONN_BEFORE_MARKET_TIMINGS,
        )

    # ---------------------------------------------------------------------------

    @staticmethod
    def is_ws_active() -> bool:
        """Check the ws connection status with last pong time"""

        # Not even a single pong recevied
        if not OptionsBrokerOrderUpdatesWebsocket._last_active_at:
            return False

        # time interval between current time and last pong time less than the max pong skip time, then declare ws active
        if (int(time.time()) - OptionsBrokerOrderUpdatesWebsocket._last_active_at) < websocket_config.DEFAULT_PING_INTERVAL_SEC * websocket_config.MAX_PONG_SKIP_FOR_ACTIVE_STATUS:
            return True

        return False
