"""Base connection class for SignalR WebSockets."""

import asyncio
import logging
import threading
from abc import ABC, abstractmethod

# This is a placeholder import - in real implementation, you'd use signalrcore or similar
from signalrcore.hub_connection_builder import HubConnectionBuilder

logger = logging.getLogger(__name__)


class HubConnection(ABC):
    """Base class for SignalR hub connections."""

    def __init__(self, client, base_hub_url, hub_path):
        """
        Initialize a hub connection.

        Args:
            client: The ProjectXClient instance
            base_hub_url (str): The base URL for the WebSocket hub
            hub_path (str): The specific hub path (e.g., '/hubs/user')
        """
        self._client = client
        self.base_hub_url = base_hub_url
        self.hub_path = hub_path
        self.hub_url = f"{base_hub_url}{hub_path}"

        # Initialize connection but don't start yet
        self._connection = None
        self._is_connected = False
        self._handlers = {}  # Event handlers

    def build_connection(self):
        """
        Build the SignalR hub connection.

        This creates the connection object but doesn't start it yet.

        Returns:
            The hub connection object
        """
        # Get the current auth token
        token = self._client.auth.token

        # Build the connection with the token
        connection = (
            HubConnectionBuilder()
            .with_url(f"{self.hub_url}?access_token={token}")
            .with_automatic_reconnect()
            .build()
        )

        # Set up basic event handlers
        connection.on_open(self._on_connection_open)
        connection.on_close(self._on_connection_close)
        connection.on_reconnect(self._on_reconnection)
        connection.on_error(self._on_error)

        return connection

    def start(self):
        """
        Start the hub connection.

        This establishes the WebSocket connection and subscribes to events.

        Returns:
            bool: True if connection started successfully
        """
        if self._is_connected:
            logger.info("Connection already started")
            return True

        try:
            if not self._connection:
                self._connection = self.build_connection()

            # Register event handlers
            self._register_handlers()

            # Start the connection
            self._connection.start()
            return True

        except Exception as e:
            logger.error(f"Failed to start connection: {str(e)}")
            return False

    def stop(self):
        """
        Stop the hub connection.

        This closes the WebSocket connection.

        Returns:
            bool: True if connection stopped successfully
        """
        if not self._is_connected or not self._connection:
            logger.info("Connection already stopped or not started")
            return True

        try:
            self._connection.stop()
            self._is_connected = False
            return True

        except Exception as e:
            logger.error(f"Failed to stop connection: {str(e)}")
            return False

    @abstractmethod
    def _register_handlers(self):
        """
        Register event handlers for the connection.

        This should be implemented by subclasses to register
        specific event handlers for the hub.
        """
        pass

    def _on_connection_open(self):
        """Handle the connection open event."""
        self._is_connected = True
        logger.info(f"Connection opened to {self.hub_url}")

        # Perform any post-connection setup
        self._on_connected()

    def _on_connection_close(self):
        """Handle the connection close event."""
        self._is_connected = False
        logger.info(f"Connection closed to {self.hub_url}")

    def _on_reconnection(self):
        """Handle the reconnection event."""
        self._is_connected = True
        logger.info(f"Reconnected to {self.hub_url}")

        # Resubscribe to events after reconnection
        self._on_connected()

    def _on_error(self, error):
        """
        Handle connection errors.

        Args:
            error: The error object
        """
        err_str = str(error)
        logger.error(f"Connection error: {err_str}")

    @abstractmethod
    def _on_connected(self):
        """
        Perform actions after connection is established.

        This is called both on initial connection and reconnection.
        Subclasses should implement this to perform any necessary
        subscriptions or other setup.
        """
        pass

    def invoke(self, method, *args):
        """
        Invoke a hub method.

        Args:
            method (str): The hub method name
            *args: Arguments to pass to the method

        Returns:
            The result of the method call

        Raises:
            Exception: If the connection is not established or the call fails
        """
        if not self._is_connected or not self._connection:
            raise Exception("Not connected to hub")

        return self._connection.send(method, args)

    def on(self, event, handler):
        """
        Register a handler for a hub event.

        Args:
            event (str): The event name
            handler (callable): The handler function

        Returns:
            self: For method chaining
        """
        if not self._handlers.get(event):
            self._handlers[event] = []

        self._handlers[event].append(handler)

        # If already connected, register with the connection
        if self._is_connected and self._connection:
            self._connection.on(event, handler)

        return self


class SignalRConnection:
    """SignalR connection for ProjectX Gateway API real-time data."""

    def __init__(self, hub_url, access_token, connection_callback=None):
        """
        Initialize a SignalR connection.

        Args:
            hub_url (str): The WebSocket hub URL
            access_token (str): JWT authentication token
            connection_callback (callable, optional): Callback to invoke when connection is
                established or reconnected
        """
        self.hub_url = hub_url
        self.access_token = access_token
        self._connection = self._build_connection()
        self._is_connected = False
        self._handlers = {}
        self._lock = threading.Lock()
        self._connection_callback = connection_callback

        # Add circuit breaker state to prevent reconnection storms
        self._reconnection_state = {
            "reconnection_active": False,
            "reconnect_attempts": 0,
            "max_reconnect_attempts": 10,  # Circuit breaker - stop after 10 failures
            "last_reconnect_time": 0.0,
            "min_reconnect_interval": 5,  # Minimum 5 seconds between attempts
            "consecutive_failures": 0,
            "circuit_breaker_time": 0.0,  # When circuit breaker was triggered
            "circuit_breaker_duration": 300,  # 5 minutes circuit breaker
        }

    def _build_connection(self):
        """
        Build the SignalR connection.

        Returns:
            The SignalR connection object
        """
        # Build without automatic reconnection since we handle it manually (like raw test)
        return (
            HubConnectionBuilder()
            .with_url(f"{self.hub_url}?access_token={self.access_token}")
            .build()
        )

    async def start(self):
        """
        Start the SignalR connection.

        This method is asynchronous and returns when the connection
        is established.

        Raises:
            Exception: If connection fails
        """
        if self._is_connected:
            logger.debug("SignalR connection already started")
            return

        try:
            # Set up handlers for connection events
            self._connection.on_open(self._on_connection_open)
            self._connection.on_close(self._on_connection_close)
            self._connection.on_error(self._on_error)

            # Register all existing event handlers
            self._register_handlers()

            # Start the connection - note: this returns a boolean, not a coroutine
            # so we don't await it
            result = self._connection.start()
            if not result:
                raise Exception("Failed to start SignalR connection")

            # Wait for connection to be established with a timeout
            max_wait_time = 30  # seconds
            start_time = asyncio.get_event_loop().time()

            while not self._is_connected:
                # Check if we've exceeded the timeout
                if asyncio.get_event_loop().time() - start_time > max_wait_time:
                    self._connection.stop()
                    raise TimeoutError(f"Connection timed out after {max_wait_time} seconds")

                # Small sleep to avoid busy waiting
                await asyncio.sleep(0.1)

            logger.info(f"SignalR connection established to {self.hub_url}")

        except Exception as e:
            logger.error(f"Failed to start SignalR connection: {str(e)}")
            raise e

    async def stop(self):
        """
        Stop the SignalR connection.

        This method is asynchronous and returns when the connection
        is closed.
        """
        if not self._is_connected:
            logger.debug("SignalR connection already stopped")
            return

        try:
            # Stop the connection - note: this returns a boolean, not a coroutine
            result = self._connection.stop()
            if not result:
                # This might be normal behavior for some SignalR implementations
                logger.debug("SignalR connection stop returned False (may be normal)")
            else:
                logger.debug("SignalR connection stop returned True")

            # Connection should be marked as closed by the on_close handler,
            # but we'll set it here as well to be sure
            self._is_connected = False
            logger.info(f"SignalR connection closed to {self.hub_url}")
        except Exception as e:
            logger.warning(f"Exception during SignalR connection stop: {str(e)}")
            # Still mark as disconnected since we tried to stop it
            self._is_connected = False

    def is_connected(self):
        """
        Check if the connection is active.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected

    def on(self, event, callback):
        """
        Register a callback for a hub event.

        Args:
            event (str): Event name
            callback (callable): Callback function

        Returns:
            self: For method chaining
        """
        with self._lock:
            if event not in self._handlers:
                self._handlers[event] = []

            self._handlers[event].append(callback)

            # If already connected, register with the connection immediately
            if self._is_connected:
                self._connection.on(event, callback)

        return self

    async def invoke(self, method, *args):
        """
        Invoke a hub method.

        Args:
            method (str): Hub method name
            *args: Arguments to pass to the method

        Returns:
            The result of the method invocation

        Raises:
            Exception: If not connected or method invocation fails
        """
        if not self._is_connected:
            raise Exception("Not connected to SignalR hub")

        try:
            # Log the raw args for debugging
            logger.debug(f"Invoking hub method {method} with args: {args}")

            # For signalrcore methods, we need to ensure arguments are in a list
            # Convert single arguments to a list containing that argument
            if len(args) == 1 and not isinstance(args[0], list):
                # Single non-list argument, wrap it in a list
                send_args = [args[0]]
            elif len(args) > 1:
                # Multiple arguments, put them all in a list
                send_args = list(args)
            else:
                # Either empty args or a single list argument
                send_args = args[0] if args and isinstance(args[0], list) else list(args)

            logger.debug(f"Final args for {method}: {send_args}")

            # Check if send is a coroutine function or a regular function
            conn_send = self._connection.send
            if asyncio.iscoroutinefunction(conn_send):
                sent_result = await conn_send(method, send_args)
                return sent_result
            else:
                return conn_send(method, send_args)
        except Exception as e:
            error_msg = f"Hub error: {method}"
            logger.error(error_msg)
            raise e

    def _register_handlers(self):
        """Register all existing event handlers with the connection."""
        with self._lock:
            for event, callbacks in self._handlers.items():
                for callback in callbacks:
                    self._connection.on(event, callback)

    def _on_connection_open(self):
        """Handle connection open event."""
        self._is_connected = True
        logger.info(f"✅ SignalR connection established to {self.hub_url}")

        # Reset reconnection state on successful connection
        self._reconnection_state["reconnection_active"] = False
        self._reconnection_state["reconnect_attempts"] = 0
        self._reconnection_state["consecutive_failures"] = 0
        self._reconnection_state["circuit_breaker_time"] = 0.0

        # Register event handlers (needed for both initial and reconnection)
        logger.debug("Registering event handlers with SignalR connection")
        self._register_handlers()

        # Call the connection callback if provided (this triggers user hub _on_connected)
        if self._connection_callback:
            try:
                self._connection_callback()
            except Exception as e:
                logger.error("Error in connection callback: " + str(e))

    def _on_connection_close(self):
        """Handle connection close event."""
        self._is_connected = False
        logger.info(f"SignalR connection closed to {self.hub_url}")

        # Use the same manual reconnection strategy as raw_user_test.py
        # This is more reliable than SignalR's built-in automatic reconnection
        self._attempt_manual_reconnection()

    def _on_error(self, error):
        """
        Handle connection error event.

        Args:
            error: The error object
        """
        err_str = str(error)
        logger.error(f"SignalR connection error: {err_str}")

    def _attempt_manual_reconnection(self):
        """
        Attempt manual reconnection with circuit breaker to prevent reconnection storms.

        This implements proper rate limiting, maximum attempts, and circuit breaker
        pattern to prevent the reconnection loops seen in the logs.
        """
        import time

        # Check if reconnection is already active
        if self._reconnection_state["reconnection_active"]:
            logger.debug("Reconnection already active, skipping duplicate attempt")
            return

        # Check circuit breaker
        current_time = time.time()
        if self._reconnection_state["circuit_breaker_time"] > 0.0:
            time_since_breaker = current_time - self._reconnection_state["circuit_breaker_time"]
            if time_since_breaker < self._reconnection_state["circuit_breaker_duration"]:
                remaining_time = (
                    self._reconnection_state["circuit_breaker_duration"] - time_since_breaker
                )
                logger.warning(
                    "🚫 Circuit breaker active - reconnection disabled for %.0f more seconds",
                    remaining_time
                )
                return
            else:
                # Circuit breaker expired, reset
                logger.info("🔄 Circuit breaker expired, allowing reconnection attempts")
                self._reconnection_state["circuit_breaker_time"] = 0.0
                self._reconnection_state["consecutive_failures"] = 0

        # Check if we've hit max attempts
        if (
            self._reconnection_state["reconnect_attempts"]
            >= self._reconnection_state["max_reconnect_attempts"]
        ):
            logger.error(
                "🚫 Maximum reconnection attempts (%d) reached - triggering circuit breaker",
                self._reconnection_state['max_reconnect_attempts']
            )
            self._reconnection_state["circuit_breaker_time"] = current_time
            return

        # Check minimum interval between attempts
        time_since_last = current_time - self._reconnection_state["last_reconnect_time"]
        if time_since_last < self._reconnection_state["min_reconnect_interval"]:
            logger.debug(
                "Reconnection rate limited - %.1fs < %ds minimum",
                time_since_last,
                self._reconnection_state['min_reconnect_interval']
            )
            return

        def reconnection_worker():
            try:
                self._reconnection_state["reconnection_active"] = True
                self._reconnection_state["last_reconnect_time"] = time.time()

                reconnect_delay = 5  # Start with 5 second delay
                max_delay = 60  # Max 60 seconds between attempts

                while not self._is_connected and self._reconnection_state["reconnection_active"]:
                    try:
                        self._reconnection_state["reconnect_attempts"] += 1

                        logger.info(
                            "🔄 Attempting reconnection #%d in %d seconds...",
                            self._reconnection_state['reconnect_attempts'],
                            reconnect_delay
                        )
                        time.sleep(reconnect_delay)

                        if self._is_connected:
                            break  # Connection restored while we were waiting

                        logger.info("🔄 Creating new connection for manual reconnection...")

                        # Stop the old connection completely
                        if self._connection:
                            try:
                                self._connection.stop()
                            except Exception:
                                pass

                        # Create a completely new connection from scratch
                        self._connection = self._build_connection()

                        # Set up connection event handlers
                        self._connection.on_open(self._on_connection_open)
                        self._connection.on_close(self._on_connection_close)
                        self._connection.on_error(self._on_error)

                        # Register all existing event handlers
                        self._register_handlers()

                        # Start the new connection
                        result = self._connection.start()
                        if result:
                            logger.info("✅ Manual reconnection successful")
                            break
                        else:
                            logger.error("❌ Manual reconnection failed - will retry")
                            self._reconnection_state["consecutive_failures"] += 1

                    except Exception as e:
                        logger.error("❌ Reconnection failed: %s", e)
                        self._reconnection_state["consecutive_failures"] += 1

                        # Exponential backoff
                        reconnect_delay = min(reconnect_delay * 1.5, max_delay)

                        # Check if we should trigger circuit breaker due to consecutive failures
                        if self._reconnection_state["consecutive_failures"] >= 5:
                            logger.error(
                                "🚫 Too many consecutive failures - triggering circuit breaker"
                            )
                            self._reconnection_state["circuit_breaker_time"] = time.time()
                            break

                        continue

            finally:
                self._reconnection_state["reconnection_active"] = False
                logger.debug("Reconnection worker thread finished")

        # Start reconnection in background thread
        threading.Thread(target=reconnection_worker, daemon=True).start()

    def get_reconnection_status(self):
        """
        Get current reconnection status for debugging.

        Returns:
            dict: Current reconnection state information
        """
        import time

        current_time = time.time()

        status = self._reconnection_state.copy()
        status["is_connected"] = self._is_connected
        status["hub_url"] = self.hub_url

        # Add time remaining for circuit breaker
        if status["circuit_breaker_time"] > 0.0:
            time_since_breaker = current_time - status["circuit_breaker_time"]
            status["circuit_breaker_remaining"] = max(
                0, status["circuit_breaker_duration"] - time_since_breaker
            )
        else:
            status["circuit_breaker_remaining"] = 0

        # Add time since last reconnect attempt
        if status["last_reconnect_time"] > 0.0:
            status["time_since_last_reconnect"] = current_time - status["last_reconnect_time"]
        else:
            status["time_since_last_reconnect"] = 0

        return status

    def reset_circuit_breaker(self):
        """
        Manually reset the circuit breaker (for testing/admin purposes).

        Returns:
            bool: True if circuit breaker was reset
        """
        if self._reconnection_state["circuit_breaker_time"] > 0.0:
            logger.info("🔄 Manually resetting circuit breaker")
            self._reconnection_state["circuit_breaker_time"] = 0.0
            self._reconnection_state["consecutive_failures"] = 0
            self._reconnection_state["reconnect_attempts"] = 0
            return True
        return False

    def refresh_token(self, new_access_token):
        """
        Refresh the connection with a new access token.

        This will rebuild the connection with the new token and attempt to reconnect.

        Args:
            new_access_token (str): The new JWT access token
        """
        logger.info("Refreshing SignalR connection with new token")

        # Store current state
        was_connected = self._is_connected

        # Update the token
        self.access_token = new_access_token

        # Stop current connection if running
        if was_connected:
            try:
                self._connection.stop()
            except Exception as e:
                logger.warning(f"Error stopping connection during token refresh: {e}")

        # Rebuild connection with new token
        self._connection = self._build_connection()
        self._is_connected = False

        logger.debug("SignalR connection rebuilt with new token")
