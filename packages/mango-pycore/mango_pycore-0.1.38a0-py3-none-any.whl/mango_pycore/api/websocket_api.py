import logging
import traceback
from copy import copy

from mango_pycore.api.request import WebsocketApiRequest
from mango_pycore.api.response import Response
from mango_pycore.api.exceptions import MiddlewareShortCircuit


class WebsocketApi:
    """
    WebsocketApi class to manage websocket requests and responses.
    """

    def __init__(self, name="SAM-API-WEBSOCK"):
        self.name = name
        self._resources = {}
        self._middlewares = []
        self._debug = False
        self.log = self._config_logging()

    def _config_logging(self):
        """
        Configure logging for the Websocket Api
        """
        logger = logging.getLogger(self.name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if self._debug else logging.INFO)
        return logger

    def __call__(self, event, context, *args, **kwargs):
        """
        Handle incoming websocket events
        """
        self.log.debug(f"Received event: {event}")
        try:
            request = self._process_middlewares(WebsocketApiRequest(event, self._debug))
            function = self._resources.get(request.route_key)
            
            if not function:
                raise KeyError(f"No function registered for route key: {request.route_key}")

            response = function(request)

            if isinstance(response, Response):
                return response.to_dict()

            return response

        except Exception as e:
            self.log.error(f"Error processing event: {str(e)}")
            self.log.error(traceback.format_exc())
            raise Exception("Internal Server Error") from e

    def route(self, route_key: str):
        """
        Decorator to register a route with a specific route_key
        """
        def inner_register(function):
            self._register_route(route_key=route_key, func=function)
            return function
        return inner_register

    def middleware(self):
        """
        Decorator to register a middleware function revisar()...
        """
        def inner_register(function):
            self._register_middleware(function)
            return function
        return inner_register

    def _register_route(self, route_key, func):
        """
        Register a function to a specific route_key.
        """
        if route_key in self._resources:
            self.log.warning(f"Route Key '{route_key}' already registered. Overwriting with new function.")
        self._resources[route_key] = func

    def _register_middleware(self, func):
        """
        Register a middleware function.
        """
        self._middlewares.append(func)

    def _process_middlewares(self, request):
        """
        Process all registered middlewares on the incoming request.
        """
        for middleware in self._middlewares:
            request = middleware(request)
            if isinstance(request, MiddlewareShortCircuit):
                self.log.debug("Middleware short-circuited the request.")
                break
        return request
    def _register_middleware(self, func):
        self._middlewares.append(func)

    def _process_middlewares(self, request: WebsocketApiRequest):
        req = copy(request)
        for midd in self._middlewares:
            rslt = midd(req)
            if isinstance(rslt, WebsocketApiRequest):
                req = copy(rslt)
            if isinstance(rslt, Response):
                raise MiddlewareShortCircuit(response=rslt.to_dict())
        return req

    def _config_logging(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG if self._debug else logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(name)s::[%(levelname)s]: %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.propagate = 0
        return logger

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        self._debug = value
        self.log.setLevel(logging.DEBUG if self._debug else logging.INFO)
