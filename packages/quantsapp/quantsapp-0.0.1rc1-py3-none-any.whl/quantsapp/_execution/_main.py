# Built-in Modules
import sys
import json
import base64
import typing
import atexit
import secrets
import threading
import functools
import contextlib
import datetime as dt
import collections.abc

from dataclasses import dataclass
from urllib.parse import urlparse, urlencode


# Third-Party Modules
from pydantic import ValidationError


# Local Modules
from quantsapp import _models as generic_models
from quantsapp._websocket._models import OrderUpdatesWs

from quantsapp._execution._models import (
    QappRawSessionData_Type,
    BrokerClient,
)

from quantsapp._execution._modules._broker_login_data import BrokerLoginData
from quantsapp._version import __version__ as qapp_package_version
from quantsapp._logger import qapp_logger
from quantsapp._master_data import MasterData

from quantsapp import (
    _utils as generic_utils,
    _enums as generic_enums,
    exceptions as generic_exceptions,
)

from quantsapp._websocket._options_main_ws import OptionsMainWebsocket
from quantsapp._websocket._options_broker_order_updates_ws import OptionsBrokerOrderUpdatesWebsocket
from quantsapp._execution import _enums as execution_enums


# Execution Modules
from quantsapp._execution._modules._broker_add import AddBroker
from quantsapp._execution._modules._broker_delete import DeleteBroker
from quantsapp._execution._modules._broker_list import GetBrokers, GetMappedBrokers
from quantsapp._execution._modules._order_list import GetOrders
from quantsapp._execution._modules._order_place import PlaceOrder
from quantsapp._execution._modules._order_logs import GetOrderLogs
from quantsapp._execution._modules._order_modify import ModifyOrder
from quantsapp._execution._modules._order_cancel import CancelOrders, CancelAllOrders
from quantsapp._execution._modules._position_list import GetPositions, GetPositionsCombined
from quantsapp._execution._modules._broker_ws_conn import BrokerWsConnectionStatus, BrokerWsReConnect
from quantsapp._execution._modules._broker_list_models import (
    PayloadListAvailableBrokers_Pydantic,
    Response_ListAvailableBrokers,
    PayloadListMappedBrokers_Pydantic,
    Response_ListMappedBrokers,
)
from quantsapp._execution._modules._broker_add_models import (
    # PayloadBrokerLoginCredentials_Type,
    PayloadDhanBrokerLoginCredentials_Type,
    PayloadChoiceBrokerLoginCredentials_Type,
    PayloadDhanBrokerLoginCredentials_Pydantic,
    PayloadChoiceBrokerLoginCredentials_Pydantic,
    PayloadAddBroker_Pydantic,
    Response_AddBroker,
)
from quantsapp._execution._modules._broker_delete_models import (
    PayloadDeleteBroker_Pydantic,
    Response_DeleteBroker,
)
from quantsapp._execution._modules._order_list_models import (
    PayloadListOrdersFilters_Type,
    PayloadListOrders_Pydantic,
    PayloadListOrdersFilters_Pydantic,
    Response_ListOrders,
)
from quantsapp._execution._modules._order_place_models import (
    PayloadPlaceOrderBrokerAccounts_Type,
    PayloadPlaceOrderLeg_Type,
    PayloadPlaceOrder_Pydantic,
    PayloadPlaceOrderBrokerAccounts_Pydantic,
    PayloadPlaceOrderLeg_Pydantic,
    Response_PlaceOrder,
)
from quantsapp._execution._modules._order_modify_models import (
    PayloadModifyOrder_Pydantic,
    Response_ModifyOrder,
)
from quantsapp._execution._modules._order_cancel_models import (
    PayloadCancelOrder_Type,
    PayloadCancelOrderIds_Pydantic,
    PayloadCancelIndividualBrokerOrder_Pydantic,
    PayloadCancelOrders_Pydantic,
    Response_CancelOrders,
    PayloadCancelAllOrders_Pydantic,
    Response_CancelAllOrders,
)
from quantsapp._execution._modules._position_list_models import (
    PayloadGetPositions_Type,
    PayloadGetPositions_Pydantic,
    Response_GetPositions,
    Response_GetPositionsCombined,
)
from quantsapp._execution._modules._order_logs_models import (
    PayloadGetOrderLogs_Pydantic,
    Response_GetOrderLogs,
)
from quantsapp._execution._modules._broker_ws_conn_models import (
    PayloadGetBrokerWebsocketConnectionStatus_Pydantic,
    Response_GetBrokerWebsocketConnectionStatus,

    PayloadBrokerWebsocketReConnect_Pydantic,
    Response_BrokerWebsocketReConnect,
)

from quantsapp._api_helper._main import ApiHelper

from quantsapp._execution import _variables

from quantsapp._login import _models as login_models

# ----------------------------------------------------------------------------------------------------

@dataclass
class Execution:
    """
        Execution method to interact with Quantsapp API for trading operations

        Args:
            session_context: The session context for the user got from `Login` Method
            order_updates_callback: Callback function to get real-time order updates
    """

    session_context: login_models.SessionContext
    order_updates_callback: typing.Optional[collections.abc.Callable[[OrderUpdatesWs], typing.Any]] = None

    variables: typing.ClassVar = _variables

    # ---------------------------------------------------------------------------

    def __post_init__(self) -> None:

        self.__connect_main_ws()

        self.__connect_broker_order_updates_ws()

        self.__preprocess()

    # ---------------------------------------------------------------------------

    def __connect_main_ws(self) -> None:
        """Connect to Options Websocket to get api data"""

        # TODO change this to config
        query_params = {
            'ws_msg_type': 'api_client_login',
            'api_jwt': self.session_context.jwt,
            'portal': 'api',
            'sub_portal': 'python_sdk',
            'python_version': sys.version,
            'version': qapp_package_version,
            'country': 'in',
            'uid': generic_utils.get_mac_address(),
            'ref_id': f"{dt.datetime.now(dt.UTC):%d%m%Y}-{secrets.token_urlsafe(16)}",
        }

        url = self.__main_ws_url
        url += ('&' if urlparse(url).query else '?') + urlencode(query_params)

        _ws_conn_condition = threading.Condition()
        self.__ws_main = OptionsMainWebsocket(
            url=url,
            ws_conn_cond=_ws_conn_condition,
        )

        with _ws_conn_condition:
            self.__ws_main.start()
            _ws_conn_condition.wait()

        # On exiting the python code, close the main ws
        # TODO change the logic of handling the ws connections
        atexit.register(self.__close_ws)

    # ---------------------------------------------------------------------------

    def __connect_broker_order_updates_ws(self) -> None:
        """Connect to Broker Order updates websocket to get Realtime order updates"""

        if not self.__should_connect_broker_order_updates_ws():
            return None

        query_params = {
            'ws_msg_type': 'etoken',
            'etoken': self.__ws_main.ws_session_data['etoken'],
            'portal': 'api',
            'sub_portal': 'python_sdk',
            'python_version': sys.version,
            'version': qapp_package_version,
            'country': 'in',
            'uid': generic_utils.get_mac_address(),
            'ref_id': f"{dt.datetime.now(dt.UTC):%d%m%Y}-{secrets.token_urlsafe(16)}",
        }

        url = self.__broker_order_updates_ws_url
        url += ('&' if urlparse(url).query else '?') + urlencode(query_params)

        _ws_conn_condition = threading.Condition()
        self.__ws_broker_orders = OptionsBrokerOrderUpdatesWebsocket(
            url=url,
            ws_conn_cond=_ws_conn_condition,
            order_updates_callback=self.order_updates_callback, # type: ignore
        )

        with _ws_conn_condition:
            self.__ws_broker_orders.start()
            _ws_conn_condition.wait()

    # ---------------------------------------------------------------------------

    def __should_connect_broker_order_updates_ws(self) -> bool:
        """Check whether to Connect Broker Order updates websocket to get Realtime order updates"""

        if not self.order_updates_callback:
            qapp_logger.debug(f"Broker Update Callback func not passed, so don't need to connect to {OptionsBrokerOrderUpdatesWebsocket.__name__}")
            return False

        if not OptionsBrokerOrderUpdatesWebsocket.should_connect_broker_order_updates_ws():
            qapp_logger.debug(f"Trading not allowed, so don't need to connect to {OptionsBrokerOrderUpdatesWebsocket.__name__}")
            return False

        return True

    # ---------------------------------------------------------------------------

    @property
    def __main_ws_url(self) -> str:
        """Parse and get the main ws url from session id"""

        return self.__qapp_raw_session_data['ws']

    # ---------------------------------------------------------------------------

    @property
    def __broker_order_updates_ws_url(self) -> str:
        """Parse and get the Broker Order Updates ws url from session id"""

        return self.__qapp_raw_session_data['ws_order_updates']

    # ---------------------------------------------------------------------------

    @functools.cached_property
    def __qapp_raw_session_data(self) -> QappRawSessionData_Type:
        """Parse the raw session data from session_id and return it"""

        return json.loads(base64.b64decode(self.session_context.jwt.split('.')[1] + '=='))['qapp']

    # ---------------------------------------------------------------------------

    def __close_ws(self) -> None:

        _close_ws = ('ws_main', 'ws_broker_orders')

        for ws_name in _close_ws:
            with contextlib.suppress(Exception):
                if hasattr(self, ws_name):
                    getattr(self, ws_name).close_ws()

    # ---------------------------------------------------------------------------

    def __preprocess(self) -> None:
        """Do preprocess after connected to websocket"""

        self.__api_helper = ApiHelper(ws=self.__ws_main)

        # Master data should be processed first, 
        # as it is the based for all other preprocessing
        self.__update_master_data()

        self.__update_get_available_brokers()

        # Invoke the api helper with consolidated requests to optimize query
        self.__api_helper.invoke_consolidated_api()

        self.__update_local_cache_files()

    # ---------------------------------------------------------------------------

    def __update_master_data(self) -> None:
        """Download and update master data to memory"""

        # Get the master data and push it to memory
        MasterData().update_master_data(
            api_helper=self.__api_helper,
        )

    # ---------------------------------------------------------------------------

    def __update_get_available_brokers(self) -> None:
        """Download and update the broker login data to memory"""

        BrokerLoginData().update_broker_login_data(
            api_helper=self.__api_helper,
        )

    # ---------------------------------------------------------------------------

    def __update_local_cache_files(self) -> None:
        """Get the local cache files and push it to in-memory cache"""

        for name in dir(self):
            with contextlib.suppress(Exception):
                if name.startswith(f"_{self.__class__.__name__}__get_local_cache_"):
                    method = getattr(self, name)
                    method()

    # ---------------------------------------------------------------------------

    def __get_local_cache_broker_orders(self) -> None: # type: ignore[reportUnusedFunction] - This is being used by '__update_local_cache_files'
        GetOrders.update_cache_data_to_memory()        

    def __get_local_cache_broker_positions(self) -> None: # type: ignore[reportUnusedFunction] - This is being used by '__update_local_cache_files'
        GetPositions.get_data_from_local_file()        

    def __get_local_cache_broker_positions_combined(self) -> None: # type: ignore[reportUnusedFunction] - This is being used by '__update_local_cache_files'
        GetPositionsCombined.get_data_from_local_file()        

    # ---------------------------------------------------------------------------

    def __error_handling(
            self,
            error: ValidationError | generic_exceptions.QuantsappException | Exception,
            response: generic_models._BaseResponse,
        ) -> None:
        """Handle the error and add required response error data"""

        if isinstance(error, ValidationError):
            response.error.code = generic_enums.ErrorCodes.INVALID_INPUT
            response.error.msg = str(error)
        elif isinstance(error, generic_exceptions.QuantsappException):
            response.error.code = error.error_code
            response.error.msg = str(error)
        else:
            response.error.code = generic_enums.ErrorCodes.SDK_CODE_FAILURE
            response.error.msg = 'Something went wrong!'

    # ---------------------------------------------------------------------------

    def __response_post_process(self, response: generic_models._BaseResponse) -> None:
        """Do the final processing on Response object"""

        # Set the error as None, if its success
        if response.success is True:
            response.error = None

    # ---------------------------------------------------------------------------

    def list_available_brokers(self) -> Response_ListAvailableBrokers:
        """
        list the brokers based on login mode (ui only & code based)

        Returns:
            Response object with list of available brokers

        Example:
            ```py
            available_brokers = qapp_execution.list_available_brokers()

            if available_brokers.success:
                print(available_brokers.body)
                '''sample
                {
                    'access_token_login': [
                        Broker.CHOICE,
                        Broker.DHAN,
                    ],
                    'oauth_login': [
                        Broker.MSTOCK,
                        Broker.FIVEPAISA,
                        Broker.FIVEPAISA_XTS,
                        Broker.FYERS,
                        Broker.ZERODHA,
                        Broker.MOTILAL_OSWAL,
                        Broker.UPSTOX,
                        Broker.ALICEBLUE,
                        Broker.NUVAMA,
                    ]
                }
                '''
            else:
                print(f"Error on listing available brokers -> {available_brokers.error}")

            if qapp_execution.variables.Broker.CHOICE in available_brokers.body['access_token_login']:
                print('CHOICE broker can be added to Quantsapp via this SDK')

            if qapp_execution.variables.Broker.MSTOCK in available_brokers.body['access_token_login']:
                print("MSTOCK broker can't be added to Quantsapp via this SDK. Please add it via https://web.quantsapp.com/broker")
            ```
        """        

        _resp = Response_ListAvailableBrokers(
            success=False,
        )
        try:
            _resp.body = GetBrokers(
                ws=self.__ws_main,
                payload=PayloadListAvailableBrokers_Pydantic(),
            ).list_available_brokers()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)

        return _resp

    # ---------------------------------------------------------------------------

    def list_mapped_brokers(
            self,
            resync_from_broker: bool = False,
            from_cache: bool = True,
        ) -> Response_ListMappedBrokers:
        """
        List all mapped brokers.

        Args:
            resync_from_broker: Whether to resync from the broker. Defaults to False.
            from_cache: Whether to get data from cache. Defaults to True.

        Returns:
            The response object containing the list of mapped brokers.

        Example:
            ```py
            mapped_brokers_resp = qapp_execution.list_mapped_brokers(
                resync_from_broker=False,
                from_cache=False,
            )
            if mapped_brokers_resp.success:
                print(mapped_brokers_resp.body)
                '''sample
                {
                    'brokers': {
                        Broker.CHOICE: {
                            '<CLIENT_ID>': {
                                'margin': {
                                    Exchange.NSE_FNO: 7958.67,
                                    'dt': datetime.datetime(2025, 5, 23, 13, 8, 1, tzinfo=datetime.timezone.utc)
                                },
                                'name': '<NAME>',
                                'role': BrokerRole.EXECUTOR,
                                'valid': True,
                                'validity': datetime.datetime(2025, 6, 19, 11, 57, 18, tzinfo=datetime.timezone(datetime.timedelta(seconds=19800), 'IST'))
                            }
                        },
                    },
                    'next_margin': datetime.datetime(2025, 5, 23, 13, 23, tzinfo=datetime.timezone.utc),
                    'version': 42
                }
                '''
            else:
                print(f"Error on getting mapped brokers -> {mapped_brokers_resp.error}")
            ```
        """

        _resp = Response_ListMappedBrokers(
            success=False,
        )
        try:
            _resp.body = GetMappedBrokers(
                ws=self.__ws_main,
                payload=PayloadListMappedBrokers_Pydantic(
                    resync_from_broker=resync_from_broker,
                    from_cache=from_cache,
                ),
            ).list_brokers()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)

        return _resp

    # ---------------------------------------------------------------------------

    def add_broker(
            self,
            broker: execution_enums.Broker,
            login_credentials: PayloadDhanBrokerLoginCredentials_Type | PayloadChoiceBrokerLoginCredentials_Type,
            delete_previous_users: bool = False,
            update_owner: bool = False,
        ) -> Response_AddBroker:
        """
        Add a broker account to Quantsapp account

        Args:
            broker: The broker to add.
            login_credentials: The login credentials for the broker.
            delete_previous_users: Whether to delete previous users
            update_owner: Whether to update the owner

        Returns:
            The response object containing the result of the add broker operation.

        Example:
            > ##### DHAN
            ```py
            add_dhan_broker_resp = qapp_execution.add_broker(
                broker=qapp_execution.variables.Broker.DHAN,
                login_credentials={
                    'access_token': '<DHAN_ACCESS_TOKEN>',
                },
            )
            if add_dhan_broker_resp.success:
                print(f"Dhan Broker added -> {add_dhan_broker_resp.body = }")
            else:
                print(f"Dhan broker failed to add -> {add_dhan_broker_resp.error}")
            ```

            > ##### CHOICE
            ```py
            add_choice_broker_resp = qapp_execution.add_broker(
                broker=qapp_execution.variables.Broker.CHOICE,
                login_credentials={
                    'mobile': '1234567890',
                    'client_access_token': '<CHOICE_ACCESS_TOKEN>',
                },
            )
            if add_choice_broker_resp.success:
                print(f"Choice Broker added -> {add_choice_broker_resp.body = }")
            else:
                print(f"Choice broker failed to add -> {add_choice_broker_resp.error}")
            ```
        """

        _resp = Response_AddBroker(
            success=False,
        )
        try:
            # Parse Login Credentials
            match broker:
                case execution_enums.Broker.DHAN:
                    _login_credentials = PayloadDhanBrokerLoginCredentials_Pydantic.model_validate(login_credentials)
                case execution_enums.Broker.CHOICE:
                    _login_credentials = PayloadChoiceBrokerLoginCredentials_Pydantic.model_validate(login_credentials)
                case _:
                    raise generic_exceptions.InvalidInputError(f"Invalid Broker ({broker}) for 'access_token' login!")

            _resp.body = AddBroker(
                ws=self.__ws_main,
                payload=PayloadAddBroker_Pydantic(
                    broker=broker,
                    login_credentials=_login_credentials,
                    delete_previous_users=delete_previous_users,
                    update_owner=update_owner,
                ),
            ).login()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)

        return _resp

    # ---------------------------------------------------------------------------

    def delete_broker(
            self,
            broker: execution_enums.Broker,
            client_id: str,
        ) -> Response_DeleteBroker:
        """
        Delete the broker account from Quantsapp, if exists

        Args:
            broker: The broker to delete.
            client_id: The client ID of the broker account to delete.

        Returns:
            The response object containing the result of the delete broker operation.

        Example:
            ```py
            broker_delete_resp = qapp_execution.delete_broker(
                broker=quantsapp.Broker.CHOICE,
                client_id='<CLIENT_ID>',
            )
            if broker_delete_resp.success:
                print(f"Broker deleted -> {broker_delete_resp.body = }")
            else:
                print(f"Broker failed to delete -> {broker_delete_resp.error}")
            ```
        """

        _resp = Response_DeleteBroker(
            success=False,
        )

        try:
            _resp.body = DeleteBroker(
                ws=self.__ws_main,
                payload=PayloadDeleteBroker_Pydantic(
                    broker_client=BrokerClient(
                        broker=broker,
                        client_id=client_id,
                    )
                )
            ).delete()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)

        return _resp

    # ---------------------------------------------------------------------------

    def get_orderbook(
            self,
            broker: execution_enums.Broker,
            client_id: str,
            resync_from_broker: bool = False,
            from_cache: bool = True,
            ascending: bool = False,
            filters: typing.Optional[PayloadListOrdersFilters_Type] = None,
        ) -> Response_ListOrders:
        """
        Retrieve the order book for a specific broker account.

        Args:
            broker: The broker to retrieve the order book for.
            client_id: The client ID of the broker account to retrieve the order book for.
            resync_from_broker: Whether to resync the order book from the broker.
            from_cache: Whether to retrieve the order book from cache.
            ascending: Whether to sort the order book in ascending order.
            filters: Optional filters to apply to the order book.

        Returns:
            The response object containing the result of the retrieve order book operation.

        Example:
            ```py
            get_orders_resp = qapp_execution.get_orderbook(
                broker=qapp_execution.variables.Broker.DHAN,
                client_id='<CLIENT_ID>',
                ascending=False,
                from_cache=True,            # Return the orders from either local cache or Quantsapp server
                resync_from_broker=False,   # Resync the orders from Broker api again

                # Optional (any combo of below filters)
                filters={
                    'product': qapp_execution.variables.Order.ProductType.INTRADAY,
                    'order_status': qapp_execution.variables.Order.Status.CANCELLED,
                    'order_type': qapp_execution.variables.Order.OrderType.LIMIT,
                    'instrument': 'NIFTY:22-May-25:p:250000',  # instrument structure = 'SYMBOL:EXPIRY:OPTION_TYPE:STRIKE'
                },
            )
            if get_orders_resp.success:
                print(get_orders_resp.body)
                '''sample
                [
                    {
                        'b_orderid': '42250523454209',
                        'b_usec_update': datetime.datetime(2025, 5, 23, 9, 50, 44, tzinfo=datetime.timezone.utc),
                        'broker_client': BrokerClient(broker=Broker.DHAN, client_id='1100735577'),
                        'buy_sell': OrderBuySell.BUY,
                        'e_orderid': '1200000163510266',
                        'instrument': 'NIFTY:05-Jun-25:c:25650',
                        'o_ctr': 10,
                        'order_status': OrderStatus.CANCELLED,
                        'order_type': OrderType.LIMIT,
                        'price': 1.45,
                        'product_type': OrderProductType.NRML,
                        'q_usec': datetime.datetime(2025, 5, 23, 9, 50, 44, tzinfo=datetime.timezone.utc),
                        'qty': 75,
                        'qty_filled': 0,
                        'stop_price': 0.0,
                        'userid': 500131
                    },
                ]
                '''
            else:
                print(f"Error on order listing -> {get_orders_resp.error}")
            ```
        """

        _resp = Response_ListOrders(
            success=False,
        )

        try:
            # Set default filter
            _filters: PayloadListOrdersFilters_Type = filters or {}  # type: ignore

            _resp.body = GetOrders(
                ws=self.__ws_main,
                payload=PayloadListOrders_Pydantic(
                    broker_client=BrokerClient(
                        broker=broker,
                        client_id=client_id,
                    ),
                    ascending=ascending,
                    from_cache=from_cache,
                    resync_from_broker=resync_from_broker,
                    filters=PayloadListOrdersFilters_Pydantic(
                        product=_filters.get('product'),
                        order_status=_filters.get('order_status'),
                        order_type=_filters.get('order_type'),
                        instrument=_filters.get('instrument'),
                    ),
                ),
            ).get_orders()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp

    # ---------------------------------------------------------------------------

    def place_order(
            self,
            broker_accounts: list[PayloadPlaceOrderBrokerAccounts_Type],
            product: execution_enums.OrderProductType,
            order_type: execution_enums.OrderType,
            validity: execution_enums.OrderValidity,
            legs: list[PayloadPlaceOrderLeg_Type],
            exchange: execution_enums.Exchange = execution_enums.Exchange.NSE_FNO,
            margin_benefit: bool = True,
        ) -> Response_PlaceOrder:
        """
        Place an order on specific broker accounts

        Args:
            broker_accounts: The list of broker accounts to place the order for.
            product: The product to place the order for.
            order_type: The type of order to place.
            validity: The validity of the order.
            legs: The legs of the order.
            exchange: The exchange to place the order on.
            margin_benefit: Whether to apply margin benefit.

        Returns:
            The response object containing the result of the place order operation.

        Example:
            ```py
            place_order_resp = qapp_execution.place_order(
                broker_accounts=[
                    {
                        'broker': qapp_execution.variables.Broker.CHOICE,
                        'client_id': '<CLIENT_ID>',
                        'lot_multiplier': 1,  # Optional - Default is 1
                    }
                ],
                exchange=qapp_execution.variables.Exchange.NSE_FNO,
                product=qapp_execution.variables.Order.ProductType.NRML,
                order_type=qapp_execution.variables.Order.OrderType.LIMIT,
                validity=qapp_execution.variables.Order.Validity.DAY,
                margin_benefit=True,  # Optional - Default = True
                legs=[
                    {
                        'qty': 75,
                        'price': 0.05,
                        'instrument': 'NIFTY:26-Jun-25:c:26500',  # Call Option
                        'buy_sell': 'b',  # Buy='b', Sell='s'
                        # 'stop_price': 5.4,  # Only for Stop Loss Limit Order
                    },
                    {
                        'qty': 75,
                        'price': 0.05,
                        'instrument': 'NIFTY:26-Jun-25:p:23500',  # Put Option
                        'buy_sell': 's',
                    },
                    {
                        'qty': 75,
                        'price': 25100,
                        'instrument': 'NIFTY:26-Jun-25:x',  # Future
                        'buy_sell': 'b',
                    },
                ],
            )
            if place_order_resp.success:
                print(place_order_resp.body)
            else:
                print(f"Error on placing order -> {place_order_resp.error}")
            ```
        """

        _resp = Response_PlaceOrder(
            success=False,
        )
        try:
            _resp.body = PlaceOrder(
                ws=self.__ws_main,
                order=PayloadPlaceOrder_Pydantic(
                    broker_accounts=[
                        PayloadPlaceOrderBrokerAccounts_Pydantic(
                            broker_client=BrokerClient(
                                broker=broker_account['broker'],
                                client_id=broker_account['client_id'],
                            ),
                            lot_multiplier=broker_account.get('lot_multiplier', 1)
                        )
                        for broker_account in broker_accounts
                    ],
                    exchange=exchange,
                    product=product,
                    order_type=order_type,
                    validity=validity,
                    legs=[
                        PayloadPlaceOrderLeg_Pydantic(
                            qty=leg['qty'],
                            price=leg['price'],
                            instrument=generic_models._Instrument_Pydantic.from_api_str(leg['instrument']),
                            buy_sell=execution_enums.OrderBuySell(leg['buy_sell']),
                            stop_price=leg.get('stop_price'),
                        )
                        for leg in legs
                    ],
                    margin_benefit=margin_benefit,
                ),
            ).place_order()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp

    # ---------------------------------------------------------------------------

    def modify_order(
            self,
            broker: execution_enums.Broker,
            client_id: str,
            b_orderid: str,
            e_orderid: str,
            qty: int,
            price: float,
            stop_price: typing.Optional[float] = None,
        ) -> Response_ModifyOrder:
        """
        Modify an existing order on specific broker accounts

        Args:
            broker: The broker account to modify the order for.
            client_id: The client ID of the broker account to modify the order for.
            b_orderid: The broker order ID of the order to modify.
            e_orderid: The exchange order ID of the order to modify.
            qty: The new quantity for the order
            price: The new price for the order
            stop_price: The new stop loss price only incase of Stop Loss type order

        Returns:
            The response object containing the result of the modify order operation.

        Example:
            ```py
            modify_order_resp = qapp_execution.modify_order(
                broker=qapp_execution.variables.Broker.CHOICE,
                client_id='<CLIENT_ID>',
                b_orderid='<BROKER_ORDER_ID>',
                e_orderid='<EXCHANGE_ORDER_ID>',
                qty=75,
                price=0.15,
                stop_price=0.05,  # Only for Stop Loss Order
            )
            if modify_order_resp.success:
                print(modify_order_resp.body)
            else:
                print(f"Error on modifying order -> {modify_order_resp.error}")
            ```
        """

        _resp = Response_ModifyOrder(
            success=False,
        )
        try:
            _resp.body = ModifyOrder(
                ws=self.__ws_main,
                order=PayloadModifyOrder_Pydantic(
                    broker_client=BrokerClient(
                        broker=broker,
                        client_id=client_id,
                    ),
                    b_orderid=b_orderid,
                    e_orderid=e_orderid,
                    qty=qty,
                    price=price,
                    stop_price=stop_price,
                ),
            ).modify_order()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp

    # ---------------------------------------------------------------------------

    def cancel_orders(
            self,
            orders_to_cancel: list[PayloadCancelOrder_Type],
        ) -> Response_CancelOrders:
        """
        Cancel specific orders from specific broker accounts

        Args:
            orders_to_cancel: The list of orders to cancel

        Returns:
            The response object containing the result of the cancel orders operation.

        Example:
            ```py
            cancel_orders_resp = qapp_execution.cancel_orders(
                orders_to_cancel=[
                    {
                        'broker': qapp_execution.variables.Broker.CHOICE,
                        'client_id': '<CLIENT_ID>',
                        'order_ids': [
                            {
                                'b_orderid': '<BROKER_ORDER_ID>',
                                'e_orderid': '<EXCHANGE_ORDER_ID>',
                            },
                        ],
                    },
                    {
                        'broker': qapp_execution.variables.Broker.DHAN,
                        'client_id': '<CLIENT_ID>',
                        'order_ids': [
                            {
                                'b_orderid': '<BROKER_ORDER_ID>',
                                'e_orderid': '<EXCHANGE_ORDER_ID>',
                            },
                        ],
                    },
                ],
            )
            if cancel_orders_resp.success:
                print('Cancel Orders:-')
                pprint(cancel_orders_resp.body)
            else:
                print(f"Error on cancel order -> {cancel_orders_resp.error}")
            ```
        """

        _resp = Response_CancelOrders(
            success=False,
        )
        try:
            _resp.body = CancelOrders(
                ws=self.__ws_main,
                payload=PayloadCancelOrders_Pydantic(
                    orders=[
                        PayloadCancelIndividualBrokerOrder_Pydantic(
                            broker_client=BrokerClient(
                                broker=order_to_cancel['broker'],
                                client_id=order_to_cancel['client_id'],
                            ),
                            order_ids=[
                                PayloadCancelOrderIds_Pydantic(
                                    b_orderid=order_id['b_orderid'],
                                    e_orderid=order_id['e_orderid'],
                                )
                                for order_id in order_to_cancel['order_ids']
                            ],
                        )
                        for order_to_cancel in orders_to_cancel
                    ],
                ),
            ).cancel_orders()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp

    # ---------------------------------------------------------------------------

    def cancel_all_orders(
            self,
            broker: execution_enums.Broker,
            client_id: str,
        ) -> Response_CancelAllOrders:
        """
        Cancel all orders from a specific broker account

        Args:
            broker: The broker account to cancel the orders for.
            client_id: The client ID of the broker account to cancel the orders for.

        Returns:
            The response object containing the result of the cancel orders operation.

        Example:
            ```py
            cancel_all_orders_resp = qapp_execution.cancel_all_orders(
                broker=qapp_execution.variables.Broker.CHOICE,
                client_id='<CLIENT_ID>',
            )
            if cancel_all_orders_resp.success:
                print(cancel_all_orders_resp.body)
            else:
                print(f"Error on cancel all orders -> {cancel_all_orders_resp.error}")
            ```
        """

        _resp = Response_CancelAllOrders(
            success=False,
        )
        try:
            _resp.body = CancelAllOrders(
                ws=self.__ws_main,
                payload=PayloadCancelAllOrders_Pydantic(
                    broker_client=BrokerClient(
                        broker=broker,
                        client_id=client_id,
                    ),
                ),
            ).cancel_all_orders()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp

    # ---------------------------------------------------------------------------

    def get_positions(
            self,
            broker_clients: list[PayloadGetPositions_Type],
            resync_from_broker: bool = False,
            from_cache: bool = True,
        ) -> Response_GetPositions:
        """
        Get positions from a specific broker account

        Args:
            broker_clients: The list of broker clients to get positions for
            resync_from_broker: Whether to resync positions from the broker
            from_cache: Whether to get positions from cache

        Returns:
            The response object containing the result of the get positions operation.

        Example:
            ```py
            get_positions_resp = qapp_execution.get_positions(
                broker_clients=[
                    {
                        'broker': qapp_execution.variables.Broker.MSTOCK,
                        'client_id': '<CLIENT_ID>',
                    },
                    {
                        'broker': qapp_execution.variables.Broker.FIVEPAISA,
                        'client_id': '<CLIENT_ID>',
                    },
                ],
                resync_from_broker=False,
                from_cache=True,
            )
            if get_positions_resp.success:
                print(get_positions_resp.body)
            else:
                print(f"Error on get positions -> {get_positions_resp.error}")
            ```
        """

        _resp = Response_GetPositions(
            success=False,
        )
        try:
            _resp.body = GetPositions(
                ws=self.__ws_main,
                payload=PayloadGetPositions_Pydantic(
                    broker_clients=[
                        BrokerClient(
                            broker=broker_client['broker'],
                            client_id=broker_client['client_id'],
                        )
                        for broker_client in broker_clients
                    ],
                    resync_from_broker=resync_from_broker,
                    from_cache=from_cache,
                ),
            ).get_positions()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp

    # ---------------------------------------------------------------------------

    def get_positions_combined(
            self,
            broker_clients: list[PayloadGetPositions_Type],
            resync_from_broker: bool = False,
            from_cache: bool = True,
        ) -> Response_GetPositionsCombined:
        """
        Get positions combinely from the specific broker accounts

        Args:
            broker_clients: The list of broker clients to get positions for
            resync_from_broker: Whether to resync positions from the broker
            from_cache: Whether to get positions from cache

        Returns:
            The response object containing the result of the get positions combined operation.

        Example:
            ```py
            get_positions_consolidated_resp = qapp_execution.get_positions_combined(
                broker_clients=[
                    {
                        'broker': qapp_execution.variables.Broker.MSTOCK,
                        'client_id': '<CLIENT_ID>',
                    },
                    {
                        'broker': qapp_execution.variables.Broker.CHOICE,
                        'client_id': '<CLIENT_ID>',
                    },
                ],
                resync_from_broker=False,
                from_cache=True,
            )
            if get_positions_consolidated_resp.success:
                print(get_positions_consolidated_resp.body)
            else:
                print(f"Error on get consolidated positions -> {get_positions_consolidated_resp.error}")
            ```
        """

        _resp = Response_GetPositionsCombined(
            success=False,
        )
        try:
            _resp.body = GetPositionsCombined(
                ws=self.__ws_main,
                payload=PayloadGetPositions_Pydantic(
                    broker_clients=[
                        BrokerClient(
                            broker=broker_client['broker'],
                            client_id=broker_client['client_id'],
                        )
                        for broker_client in broker_clients
                    ],
                    resync_from_broker=resync_from_broker,
                    from_cache=from_cache,
                ),
            ).get_positions()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp

    # ---------------------------------------------------------------------------

    def get_order_log(
            self,
            broker: execution_enums.Broker,
            client_id: str,
            instrument: str,
            q_usec: dt.datetime,
        ) -> Response_GetOrderLogs:
        """
        Get specific order logs from broker end

        Args:
            broker: The broker account to get the order logs for
            client_id: The client ID of the broker account to get the order logs for
            instrument: The instrument to get the order logs for
            q_usec: The timestamp to get the order logs for

        Returns:
            The response object containing the result of the get order logs operation.

        """

        _resp = Response_GetOrderLogs(
            success=False,
        )
        try:
            _resp.body = GetOrderLogs(
                ws=self.__ws_main,
                payload=PayloadGetOrderLogs_Pydantic(
                    broker_client=BrokerClient(
                        broker=broker,
                        client_id=client_id,
                    ),
                    instrument=generic_models._Instrument_Pydantic.from_api_str(instrument),
                    q_usec=q_usec,
                ),
            ).get_logs()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp

    # ---------------------------------------------------------------------------

    def get_broker_websocket_status(
            self,
            broker: execution_enums.Broker,
            client_id: str,
        ) -> Response_GetBrokerWebsocketConnectionStatus:
        """
        Get Broker websocket connection status

        Args:
            broker: The broker account to get the websocket status for
            client_id: The client ID of the broker account to get the websocket status for

        Returns:
            The response object containing the result of the get websocket status operation.

        Example:
            ```py
            get_broker_ws_conn_status_resp = qapp_execution.get_broker_websocket_status(
                broker=qapp_execution.variables.Broker.MSTOCK,
                client_id='<CLIENT_ID>',
            )
            if get_broker_ws_conn_status_resp.success:
                print(get_broker_ws_conn_status_resp.body)
            else:
                print(f"Error on get ws connection status -> {get_broker_ws_conn_status_resp.error}")
            ```
        """

        _resp = Response_GetBrokerWebsocketConnectionStatus(
            success=False,
        )
        try:
            _resp.body = BrokerWsConnectionStatus(
                ws=self.__ws_main,
                payload=PayloadGetBrokerWebsocketConnectionStatus_Pydantic(
                    broker_client=BrokerClient(
                        broker=broker,
                        client_id=client_id,
                    ),
                ),
            ).get_status()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp

    # ---------------------------------------------------------------------------

    def broker_websocket_reconnect(
            self,
            broker: execution_enums.Broker,
            client_id: str,
        ) -> Response_BrokerWebsocketReConnect:
        """
        Force reconnect to broker ws

        Args:
            broker: The broker account to reconnect
            client_id: The client ID of the broker account to reconnect

        Returns:
            The response object containing the result of the reconnect operation.

        Example:
            ```py
            broker_ws_re_conn_resp = qapp_execution.broker_websocket_reconnect(
                broker=qapp_execution.variables.Broker.MSTOCK,
                client_id='<CLIENT_ID>',
            )
            if broker_ws_re_conn_resp.success:
                print(broker_ws_re_conn_resp.body)
            else:
                print(f"Error on ws re-connection -> {broker_ws_re_conn_resp.error}")
            ```
        """

        _resp = Response_BrokerWebsocketReConnect(
            success=False,
        )
        try:
            _resp.body = BrokerWsReConnect(
                ws=self.__ws_main,
                payload=PayloadBrokerWebsocketReConnect_Pydantic(
                    broker_client=BrokerClient(
                        broker=broker,
                        client_id=client_id,
                    ),
                ),
            ).reconnect()
            _resp.success = True
        except Exception as er:
            self.__error_handling(er, _resp)
        self.__response_post_process(_resp)
        return _resp
