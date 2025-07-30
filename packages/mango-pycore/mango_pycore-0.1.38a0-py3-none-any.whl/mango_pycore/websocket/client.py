import json
import logging
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from json import JSONDecodeError


class WebsocketClient:
    _instances = {}

    def __init__(self, server: str, log=logging):
        self._server = self._parse_server(server)
        self._log = log
        self._websocket = None
        self._channel = None
        self._headers = None
        self._connection_url = None

    def send(self, channel: str, message, headers=None, timeout=None):
        """
        Send a message via a persistent WebSocket connection.
        """
        if not isinstance(message, str):
            message = json.dumps(message, default=str)

        try:
            self._connect_if_needed(channel, headers, timeout)
            self._websocket.send(message)
            self._log.debug(f"Sent message to channel '{channel}'")
        except (ConnectionClosedOK, ConnectionClosedError, OSError) as e:
            self._log.warning(f"Connection lost. Attempting to reconnect. Reason: {str(e)}")
            self._close()
            self._connect_if_needed(channel, headers, timeout)
            self._websocket.send(message)
        except Exception as e:
            self._log.error(f"Unexpected error sending message: {e}")
            raise

    def wait_message(self, channel: str, timeout=30, headers=None):
        """
        Wait and receive a message from a WebSocket connection.
        """
        try:
            self._connect_if_needed(channel, headers, timeout)
            message = self._websocket.recv(timeout=timeout)
            try:
                return json.loads(message)
            except JSONDecodeError:
                return message
        except TimeoutError:
            return None
        except Exception as e:
            self._log.error(f"Error waiting for message: {str(e)}")
            return None

    def _connect_if_needed(self, channel: str, headers=None, timeout=None):
        """
        Establish a WebSocket connection if not already connected or if channel changes.
        """
        if self._websocket and self._channel == channel:
            return  # Connection is valid and same channel

        self._close()

        self._channel = channel
        self._headers = headers if headers else {}
        self._connection_url = f"wss://{self._server}?channel={channel}"

        self._websocket = connect(
            self._connection_url,
            additional_headers=self._headers,
            open_timeout=timeout
        )
        self._log.debug(f"Connected to WebSocket channel: {channel}")

    def _close(self):
        """
        Close the current WebSocket connection if it exists.
        """
        if self._websocket:
            try:
                self._websocket.close()
                self._log.debug("Closed existing WebSocket connection.")
            except Exception as e:
                self._log.warning(f"Error closing WebSocket: {str(e)}")
        self._websocket = None
        self._channel = None

    def _parse_server(self, server):
        return server.split(":")[-1]
