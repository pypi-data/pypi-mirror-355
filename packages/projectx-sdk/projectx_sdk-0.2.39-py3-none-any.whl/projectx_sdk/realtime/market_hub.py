"""Market hub implementation for the ProjectX Gateway API real-time data."""

import asyncio
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

from projectx_sdk.realtime.connection import SignalRConnection

logger = logging.getLogger(__name__)


class MarketHub:
    """
    Market Hub for real-time market data.

    Provides methods to subscribe to and receive market data events
    such as quotes, trades, and market depth (order book).
    """

    def __init__(self, client_or_connection, base_hub_url=None, hub_url=None):
        """
        Initialize the market hub.

        This constructor supports multiple signatures for flexibility:
        1. MarketHub(client, base_hub_url) - legacy construction using client and base URL
        2. MarketHub(client, None, hub_url) - construction using client and direct hub URL
        3. MarketHub(connection) - construction using a SignalRConnection directly

        Args:
            client_or_connection: Either a ProjectXClient instance or a SignalRConnection
            base_hub_url (str, optional): The base hub URL (for legacy constructor)
            hub_url (str, optional): The complete hub URL (overrides base_hub_url)
        """
        # Initialize instance variables first
        self.__init_instance_vars()

        # Determine if we're using the new or legacy constructor
        if isinstance(client_or_connection, SignalRConnection):
            # New constructor with SignalRConnection
            self._connection = client_or_connection
            self._is_connected = self._connection.is_connected()
            self._owns_connection = False
        else:
            # Constructor with client and URL
            self._client = client_or_connection
            self._owns_connection = True

            if hub_url:
                # Direct hub URL provided
                self.hub_url = hub_url
                self.base_hub_url = None
                self.hub_path = None
            elif base_hub_url:
                # Base URL provided, construct hub URL
                self.base_hub_url = base_hub_url
                self.hub_path = "/hubs/market"
                self.hub_url = f"{base_hub_url}{self.hub_path}"
            else:
                raise ValueError(
                    "Either base_hub_url or hub_url is required when using client-based constructor"
                )

            # Initialize connection but don't start yet
            self._connection: Optional[SignalRConnection] = None  # type: ignore
            self._is_connected = False

        # Register event handlers if using direct connection
        if not self._owns_connection:
            self._register_handlers()

    def __init_instance_vars(self):
        """Initialize all instance variables."""
        self._quote_callbacks = {}
        self._trade_callbacks = {}
        self._depth_callbacks = {}
        self._subscribed_quotes = set()
        self._subscribed_trades = set()
        self._subscribed_depth = set()

        # Connection state tracking for robust reconnection
        self._connection_state = {
            "connected": False,
            "reconnect_count": 0,
            "manual_reconnect_active": False,
            "last_disconnect_time": None,
        }

    def _register_handlers(self):
        """Register event handlers for the market hub."""
        if self._connection:
            self._connection.on("GatewayQuote", self._handle_quote)
            self._connection.on("GatewayTrade", self._handle_trade)
            self._connection.on("GatewayDepth", self._handle_depth)

    def start(self):
        """
        Start the hub connection.

        This is only needed for legacy mode.

        Returns:
            bool: True if connection started successfully
        """
        if not self._owns_connection:
            logger.warning("Cannot start connection in direct connection mode")
            return True

        if self._is_connected and self._connection_state["connected"]:
            logger.info("Connection already started")
            return True

        try:
            if self._connection is None:
                self._connection = self._build_connection()

            # Register event handlers
            self._register_handlers()

            # Start the connection
            self._connection.start()
            self._is_connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to start connection: {str(e)}")
            self._connection_state["connected"] = False
            return False

    def _build_connection(self):
        """
        Build the connection for legacy mode with robust reconnection.

        Returns:
            The connection object
        """
        if not self._owns_connection:
            return self._connection

        from signalrcore.hub_connection_builder import HubConnectionBuilder

        # Get the current auth token
        token = self._client.auth.get_token()

        # Build the connection with the token and robust reconnection settings
        connection = (
            HubConnectionBuilder()
            .with_url(
                f"{self.hub_url}?access_token={token}",
                options={
                    "skip_negotiation": True,
                    "transport": "websockets",
                    "access_token_factory": lambda: self._client.auth.get_token(),
                    "timeout": 30,
                },
            )
            .with_automatic_reconnect(
                {
                    "type": "raw",
                    "keep_alive_interval": 10,
                    "reconnect_interval": 2,
                    "max_attempts": 0,  # Infinite reconnection attempts
                }
            )
            .build()
        )

        # Set up event handlers for robust connection management
        connection.on_open(lambda: self._on_connected())
        connection.on_close(lambda *args: self._on_connection_closed(*args))
        connection.on_error(lambda *args: self._on_connection_error(*args))

        return connection

    def stop(self):
        """
        Stop the hub connection.

        This is only needed for legacy mode.

        Returns:
            bool: True if connection stopped successfully
        """
        if not self._owns_connection:
            logger.warning("Cannot stop connection in direct connection mode")
            return True

        if not self._is_connected or not self._connection:
            logger.info("Connection already stopped or not started")
            return True

        try:
            # Stop manual reconnection attempts
            self._connection_state["manual_reconnect_active"] = False
            self._connection_state["connected"] = False

            self._connection.stop()
            self._is_connected = False
            return True

        except Exception as e:
            logger.error(f"Failed to stop connection: {str(e)}")
            return False

    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get the current connection status.

        Returns:
            Dict containing connection state information
        """
        return {
            "connected": self._connection_state["connected"],
            "reconnect_count": self._connection_state["reconnect_count"],
            "manual_reconnect_active": self._connection_state["manual_reconnect_active"],
            "last_disconnect_time": self._connection_state["last_disconnect_time"],
            "subscribed_quotes": len(self._subscribed_quotes),
            "subscribed_trades": len(self._subscribed_trades),
            "subscribed_depth": len(self._subscribed_depth),
        }

    def _handle_quote(self, data_or_contract_id, data=None):
        """
        Handle an incoming quote event.

        This handler supports two invocation patterns:
        1. _handle_quote(data) - where data is a dictionary with contractId and data fields
        2. _handle_quote(contract_id, data) - where contract_id is a string and data is a dictionary

        Args:
            data_or_contract_id: Either the data dict or the contract ID string
            data: The quote data (when using the second pattern)
        """
        contract_id = None
        quote_data = None

        # Determine which pattern we're using
        if data is None:
            # First pattern: data_or_contract_id is the data object
            try:
                # Check if data_or_contract_id is a string (likely a contract ID without data)
                if isinstance(data_or_contract_id, str):
                    contract_id = data_or_contract_id
                    quote_data = {}  # No data provided, use empty dict
                # Extract contract_id and data from the received data object
                elif isinstance(data_or_contract_id, list) and len(data_or_contract_id) > 0:
                    # SignalR direct format: [contract_id, data_dict]
                    if len(data_or_contract_id) >= 2 and isinstance(data_or_contract_id[0], str):
                        contract_id = data_or_contract_id[0]
                        quote_data = data_or_contract_id[1]
                    else:
                        message_data = data_or_contract_id[0]
                        # Check if the message data is a string
                        if isinstance(message_data, str):
                            contract_id = message_data
                            quote_data = {}
                        else:
                            contract_id = message_data.get("contractId")
                            quote_data = message_data.get("data", {})
                elif isinstance(data_or_contract_id, dict):
                    contract_id = data_or_contract_id.get("contractId")
                    quote_data = data_or_contract_id.get("data", {})
                else:
                    logger.error(
                        "Invalid quote data format: {} (type: {})".format(
                            data_or_contract_id, type(data_or_contract_id)
                        )
                    )
                    return
            except Exception as e:
                logger.error(f"Error parsing quote data: {e}")
                return
        else:
            # Second pattern: data_or_contract_id is the contract_id
            contract_id = data_or_contract_id
            quote_data = data

        if not contract_id:
            logger.debug("No contract ID in quote data")
            return

        if contract_id in self._quote_callbacks:
            for callback in self._quote_callbacks[contract_id]:
                try:
                    callback(contract_id, quote_data)
                except Exception as e:
                    logger.error(f"Error in quote callback: {e}")

    def _handle_trade(self, data_or_contract_id, data=None):
        """
        Handle an incoming trade event.

        This handler supports two invocation patterns:
        1. _handle_trade(data) - where data is a dictionary with contractId and data fields
        2. _handle_trade(contract_id, data) - where contract_id is a string and data is a dictionary

        Args:
            data_or_contract_id: Either the data dict or the contract ID string
            data: The trade data (when using the second pattern)
        """
        contract_id = None
        trade_data = None

        # Determine which pattern we're using
        if data is None:
            # First pattern: data_or_contract_id is the data object
            try:
                # Check if data_or_contract_id is a string (likely a contract ID without data)
                if isinstance(data_or_contract_id, str):
                    contract_id = data_or_contract_id
                    trade_data = {}  # No data provided, use empty dict
                # Extract contract_id and data from the received data object
                elif isinstance(data_or_contract_id, list) and len(data_or_contract_id) > 0:
                    # SignalR direct format: [contract_id, data_dict]
                    if len(data_or_contract_id) >= 2 and isinstance(data_or_contract_id[0], str):
                        contract_id = data_or_contract_id[0]
                        trade_data = data_or_contract_id[1]
                    else:
                        message_data = data_or_contract_id[0]
                        # Check if the message data is a string
                        if isinstance(message_data, str):
                            contract_id = message_data
                            trade_data = {}
                        else:
                            contract_id = message_data.get("contractId")
                            trade_data = message_data.get("data", {})
                elif isinstance(data_or_contract_id, dict):
                    contract_id = data_or_contract_id.get("contractId")
                    trade_data = data_or_contract_id.get("data", {})
                else:
                    logger.error(
                        "Invalid trade data format: {} (type: {})".format(
                            data_or_contract_id, type(data_or_contract_id)
                        )
                    )
                    return
            except Exception as e:
                logger.error(f"Error parsing trade data: {e}")
                return
        else:
            # Second pattern: data_or_contract_id is the contract_id
            contract_id = data_or_contract_id
            trade_data = data

        if not contract_id:
            logger.debug("No contract ID in trade data")
            return

        if contract_id in self._trade_callbacks:
            for callback in self._trade_callbacks[contract_id]:
                try:
                    callback(contract_id, trade_data)
                except Exception as e:
                    logger.error(f"Error in trade callback: {e}")

    def _handle_depth(self, data_or_contract_id, data=None):
        """
        Handle an incoming depth event.

        This handler supports two invocation patterns:
        1. _handle_depth(data) - where data is a dictionary with contractId and data fields
        2. _handle_depth(contract_id, data) - where contract_id is a string and data is a dictionary

        Args:
            data_or_contract_id: Either the data dict or the contract ID string
            data: The market depth data (when using the second pattern)
        """
        contract_id = None
        depth_data = None

        # Determine which pattern we're using
        if data is None:
            # First pattern: data_or_contract_id is the data object
            try:
                # Check if data_or_contract_id is a string (likely a contract ID without data)
                if isinstance(data_or_contract_id, str):
                    contract_id = data_or_contract_id
                    depth_data = {}  # No data provided, use empty dict
                # Extract contract_id and data from the received data object
                elif isinstance(data_or_contract_id, list) and len(data_or_contract_id) > 0:
                    # SignalR direct format: [contract_id, data_dict]
                    if len(data_or_contract_id) >= 2 and isinstance(data_or_contract_id[0], str):
                        contract_id = data_or_contract_id[0]
                        depth_data = data_or_contract_id[1]
                    else:
                        message_data = data_or_contract_id[0]
                        # Check if the message data is a string
                        if isinstance(message_data, str):
                            contract_id = message_data
                            depth_data = {}
                        else:
                            contract_id = message_data.get("contractId")
                            depth_data = message_data.get("data", {})
                elif isinstance(data_or_contract_id, dict):
                    contract_id = data_or_contract_id.get("contractId")
                    depth_data = data_or_contract_id.get("data", {})
                else:
                    logger.error(
                        "Invalid depth data format: {} (type: {})".format(
                            data_or_contract_id, type(data_or_contract_id)
                        )
                    )
                    return
            except Exception as e:
                logger.error(f"Error parsing depth data: {e}")
                return
        else:
            # Second pattern: data_or_contract_id is the contract_id
            contract_id = data_or_contract_id
            depth_data = data

        if not contract_id:
            logger.debug("No contract ID in depth data")
            return

        if contract_id in self._depth_callbacks:
            for callback in self._depth_callbacks[contract_id]:
                try:
                    callback(contract_id, depth_data)
                except Exception as e:
                    logger.error(f"Error in depth callback: {e}")

    async def subscribe_quotes(
        self, contract_id: str, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to real-time quotes for a contract.

        Args:
            contract_id: The contract ID to subscribe to
            callback: Function to call when a quote is received
        """
        logger.info(f"Subscribing to quotes for contract: {contract_id}")

        if contract_id not in self._quote_callbacks:
            self._quote_callbacks[contract_id] = []

            if self._connection:
                try:
                    await self._connection.invoke("SubscribeContractQuotes", contract_id)
                except Exception as e:
                    logger.error(f"Error subscribing to quotes: {e}")
                self._subscribed_quotes.add(contract_id)

        self._quote_callbacks[contract_id].append(callback)

    async def unsubscribe_quotes(
        self, contract_id: str, callback: Optional[Callable] = None
    ) -> None:
        """
        Unsubscribe from real-time quotes for a contract.

        Args:
            contract_id: The contract ID to unsubscribe from
            callback: Specific callback to remove, or None to remove all
        """
        logger.debug(f"Unsubscribing from quotes for contract: {contract_id}")

        if contract_id in self._quote_callbacks:
            if callback is None:
                self._quote_callbacks[contract_id] = []
                logger.debug(f"Removed all callbacks for contract {contract_id}")
            else:
                self._quote_callbacks[contract_id] = [
                    cb for cb in self._quote_callbacks[contract_id] if cb != callback
                ]
                count = len(self._quote_callbacks[contract_id])
                logger.debug(f"Removed specific callback. Remaining: {count}")

            if (
                not self._quote_callbacks[contract_id]
                and contract_id in self._subscribed_quotes
                and self._connection
            ):
                logger.debug(f"Invoking UnsubscribeContractQuotes for {contract_id}")
                try:
                    method = "UnsubscribeContractQuotes"
                    result = await self._connection.invoke(method, contract_id)
                    logger.debug(f"{method} result: {result}")
                except Exception as e:
                    logger.error(f"Error unsubscribing from quotes: {e}")
                self._subscribed_quotes.remove(contract_id)

    async def subscribe_trades(
        self, contract_id: str, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to real-time trades for a contract.

        Args:
            contract_id: The contract ID to subscribe to
            callback: Function to call when a trade is received
        """
        logger.info(f"Subscribing to trades for contract: {contract_id}")

        if contract_id not in self._trade_callbacks:
            self._trade_callbacks[contract_id] = []

            if self._connection:
                try:
                    await self._connection.invoke("SubscribeContractTrades", contract_id)
                except Exception as e:
                    logger.error(f"Error subscribing to trades: {e}")
                self._subscribed_trades.add(contract_id)

        self._trade_callbacks[contract_id].append(callback)

    async def unsubscribe_trades(
        self, contract_id: str, callback: Optional[Callable] = None
    ) -> None:
        """
        Unsubscribe from real-time trades for a contract.

        Args:
            contract_id: The contract ID to unsubscribe from
            callback: Specific callback to remove, or None to remove all
        """
        logger.debug(f"Unsubscribing from trades for contract: {contract_id}")

        if contract_id in self._trade_callbacks:
            if callback is None:
                self._trade_callbacks[contract_id] = []
                logger.debug(f"Removed all callbacks for contract {contract_id}")
            else:
                self._trade_callbacks[contract_id] = [
                    cb for cb in self._trade_callbacks[contract_id] if cb != callback
                ]
                count = len(self._trade_callbacks[contract_id])
                logger.debug(f"Removed specific callback. Remaining: {count}")

            if (
                not self._trade_callbacks[contract_id]
                and contract_id in self._subscribed_trades
                and self._connection
            ):
                logger.debug(f"Invoking UnsubscribeContractTrades for {contract_id}")
                try:
                    method = "UnsubscribeContractTrades"
                    result = await self._connection.invoke(method, contract_id)
                    logger.debug(f"{method} result: {result}")
                except Exception as e:
                    logger.error(f"Error unsubscribing from trades: {e}")
                self._subscribed_trades.remove(contract_id)

    async def subscribe_market_depth(
        self, contract_id: str, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to real-time market depth for a contract.

        Args:
            contract_id: The contract ID to subscribe to
            callback: Function to call when depth data is received
        """
        logger.info(f"Subscribing to market depth for contract: {contract_id}")

        if contract_id not in self._depth_callbacks:
            self._depth_callbacks[contract_id] = []

            if self._connection:
                try:
                    await self._connection.invoke("SubscribeContractMarketDepth", contract_id)
                except Exception as e:
                    logger.error(f"Error subscribing to market depth: {e}")
                self._subscribed_depth.add(contract_id)

        self._depth_callbacks[contract_id].append(callback)

    async def unsubscribe_market_depth(
        self, contract_id: str, callback: Optional[Callable] = None
    ) -> None:
        """
        Unsubscribe from real-time market depth for a contract.

        Args:
            contract_id: The contract ID to unsubscribe from
            callback: Specific callback to remove, or None to remove all
        """
        logger.debug(f"Unsubscribing from market depth for contract: {contract_id}")

        if contract_id in self._depth_callbacks:
            if callback is None:
                self._depth_callbacks[contract_id] = []
                logger.debug(f"Removed all callbacks for contract {contract_id}")
            else:
                self._depth_callbacks[contract_id] = [
                    cb for cb in self._depth_callbacks[contract_id] if cb != callback
                ]
                count = len(self._depth_callbacks[contract_id])
                logger.debug(f"Removed specific callback. Remaining: {count}")

            if (
                not self._depth_callbacks[contract_id]
                and contract_id in self._subscribed_depth
                and self._connection
            ):
                logger.debug(f"Invoking UnsubscribeContractMarketDepth for {contract_id}")
                try:
                    method = "UnsubscribeContractMarketDepth"
                    result = await self._connection.invoke(method, contract_id)
                    logger.debug(f"{method} result: {result}")
                except Exception as e:
                    logger.error(f"Error unsubscribing from market depth: {e}")
                self._subscribed_depth.remove(contract_id)

    async def reconnect_subscriptions(self) -> None:
        """Reestablish all active subscriptions after a reconnection."""
        logger.info("Reconnecting subscriptions")

        if not self._connection:
            logger.warning("Cannot reconnect subscriptions: no connection")
            return

        # Resubscribe to quotes
        for contract_id in self._subscribed_quotes:
            try:
                await self._connection.invoke("SubscribeContractQuotes", contract_id)
            except Exception as e:
                logger.error(f"Error reconnecting quotes for {contract_id}: {e}")

        # Resubscribe to trades
        for contract_id in self._subscribed_trades:
            try:
                await self._connection.invoke("SubscribeContractTrades", contract_id)
            except Exception as e:
                logger.error(f"Error reconnecting trades for {contract_id}: {e}")

        # Resubscribe to market depth
        for contract_id in self._subscribed_depth:
            try:
                await self._connection.invoke("SubscribeContractMarketDepth", contract_id)
            except Exception as e:
                logger.error(f"Error reconnecting market depth for {contract_id}: {e}")

    def _on_connected(self) -> None:
        """
        Handle connection established or reconnection events.

        This restores all active subscriptions after a connection is established.
        """
        self._connection_state["connected"] = True
        self._connection_state["reconnect_count"] += 1
        self._connection_state["manual_reconnect_active"] = False

        attempt_num = self._connection_state["reconnect_count"]
        logger.info(
            f"Market hub connection established (attempt #{attempt_num}) - restoring subscriptions"
        )

        # Create a task for the reconnection instead of calling it directly
        asyncio.create_task(self._reconnect_and_log_errors())

    async def _reconnect_and_log_errors(self) -> None:
        """Reconnect subscriptions and log any errors."""
        try:
            await self.reconnect_subscriptions()
            logger.info("Successfully reconnected all subscriptions")
        except Exception as e:
            logger.error(f"Error reconnecting subscriptions: {e}")

    def _on_connection_closed(self, *args):
        """Handle connection closed event with robust manual reconnection."""
        logger.warning(f"Market hub connection closed with args: {args}")
        self._connection_state["connected"] = False
        self._connection_state["last_disconnect_time"] = time.time()

        # Start manual reconnection if not already active and we own the connection
        if not self._connection_state["manual_reconnect_active"] and self._owns_connection:
            self._connection_state["manual_reconnect_active"] = True
            threading.Thread(target=self._attempt_manual_reconnection, daemon=True).start()

    def _on_connection_error(self, *args):
        """Handle connection error event with robust manual reconnection."""
        logger.error(f"Market hub connection error: {args}")
        self._connection_state["connected"] = False
        self._connection_state["last_disconnect_time"] = time.time()

        # Start manual reconnection if not already active and we own the connection
        if not self._connection_state["manual_reconnect_active"] and self._owns_connection:
            self._connection_state["manual_reconnect_active"] = True
            threading.Thread(target=self._attempt_manual_reconnection, daemon=True).start()

    def _attempt_manual_reconnection(self):
        """Attempt manual reconnection with exponential backoff."""
        reconnect_delay = 5  # Start with 5 second delay
        max_delay = 60  # Max 60 seconds between attempts

        while (
            not self._connection_state["connected"]
            and self._connection_state["manual_reconnect_active"]
        ):
            try:
                logger.info(f"Attempting manual reconnection in {reconnect_delay} seconds...")
                time.sleep(reconnect_delay)

                if self._connection_state["connected"]:
                    break  # Connection restored while we were waiting

                logger.info("Creating new hub connection for manual reconnection...")

                # Stop the old connection if it exists
                if self._connection:
                    try:
                        self._connection.stop()
                    except:
                        pass

                # Create a completely new connection
                self._connection = self._build_connection()

                # Register event handlers for the new connection
                self._register_handlers()

                # Start the new connection
                self._connection.start()

                # Connection success will be handled by _on_connected
                logger.info("Manual reconnection attempt completed")
                break

            except Exception as e:
                logger.error(f"Manual reconnection failed: {e}")
                # Exponential backoff
                reconnect_delay = min(reconnect_delay * 1.5, max_delay)
                continue

        self._connection_state["manual_reconnect_active"] = False
