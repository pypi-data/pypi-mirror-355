import logging
import types
from copy import copy

from mango_pycore.api.request import BaseRequest
from mango_pycore.api.response import Response
from mango_pycore.api.exceptions import MiddlewareShortCircuit

# Default CORS headers used for preflight requests and responses
default_cors_headers = {
    "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET, PUT, POST, PATCH, DELETE",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Max-Age": 600,
    "Content-Type": "application/json"
}


class Api:
    """
    A class to represent an API with routing and middleware capabilities.
    
    Attributes
    ----------
    cors_headers : dict
        The CORS headers to be used for preflight requests and responses.
    cors_function : function
        The function to handle CORS preflight requests.
    name : str
        The name of the API.
    _resources : dict
        A dictionary to store route functions.
    _middlewares : list
        A list to store middleware functions.
    _debug : bool
        A flag to indicate if debug mode is enabled.
    log : logging.Logger
        The logger for the API instance.

    Methods
    -------
    route(path, methods, cors=True)
        Decorator to register a route with specified path and methods.
    middleware()
        Decorator to register a middleware function.
    _register_route(path, method, cors, func)
        Register a route with the given path, method, and function.
    _register_middleware(func)
        Register a middleware function.
    _process_middlewares(request)
        Process all registered middlewares with the given request.
    _process_options_request(request)
        Handle OPTIONS requests for CORS preflight.
    _config_logging()
        Configure logging for the API instance.
    debug()
        Get or set the current debug mode status.
    """

    def __init__(self, name="SAM-API", cors_headers=None, cors_function=None):
        """
        Constructs all the necessary attributes for the Api object.

        Parameters
        ----------
        name : str, optional
            The name of the API (default is "SAM-API").
        cors_headers : dict, optional
            The CORS headers to be used ().
        cors_function : function, optional
            The function to handle CORS preflight requests .
        """
        self.cors_headers = cors_headers if cors_headers is not None and isinstance(cors_headers,
                                                                                    dict) else default_cors_headers
        self.cors_function = cors_function if cors_function is not None and isinstance(cors_function,
                                                                                       types.FunctionType) else self._process_options_request
        self.name = name
        self._resources = {}
        self._middlewares = []
        self._debug = False
        self.log = self._config_logging()

    def route(self, path: str, methods: list, cors: bool = True):
        """
        Decorator to register a route with specified path and methods.

        Parameters
        ----------
        path : str
            The URL path for the route.
        methods : list
            List of HTTP methods (GET, POST, etc.) for the route.
        cors : bool, optional
            Boolean flag to enable CORS for the route (default is True).

        Returns
        -------
        function
            Decorator function to register the route.
        """

        def inner_register(function):
            # Default route
            if path == '$default':
                self._resources['$default'] = function
                self._resources['OPTIONS /{proxy+}'] = self.cors_function
            else:
                for method in methods:
                    self._register_route(path=path, method=method, cors=cors, func=function)
            return function

        return inner_register

    def middleware(self):
        """
        Decorator to register a middleware function.

        Returns
        -------
        function
            Decorator function to register the middleware.
        """

        def inner_register(function):
            self._register_middleware(function)
            return function

        return inner_register

    def _register_route(self, path, method, cors, func):
        """
        Register a route with the given path, method, and function.

        Parameters
        ----------
        path : str
            The URL path for the route.
        method : str
            HTTP method for the route.
        cors : bool
            Boolean flag to enable CORS for the route.
        func : function
            Function to handle the route.
        """
        route_key = f"{method} {path}"
        if route_key in self._resources.keys() and method != "OPTIONS":
            self.log.warning(f"Path '{route_key}' already registered and will be replaced by last function")
        self._resources[route_key] = func
        if cors:
            route_key_proxy = "OPTIONS /{proxy+}"
            route_key = f"OPTIONS {path}"
            self._resources[route_key_proxy] = self.cors_function
            self._resources[route_key] = self.cors_function

    def _register_middleware(self, func):
        """
        Register a middleware function.

        Parameters
        ----------
        func : function
            Middleware function to be added.
        """
        self._middlewares.append(func)

    def _process_middlewares(self, request):
        """
        Process all registered middlewares with the given request.

        Parameters
        ----------
        request : BaseRequest
            The incoming request object.

        Returns
        -------
        BaseRequest
            Modified request after processing through middlewares.

        Raises
        ------
        MiddlewareShortCircuit
            If a middleware returns a Response.
        """
        req = copy(request)
        for midd in self._middlewares:
            rslt = midd(req)
            if isinstance(rslt, BaseRequest):
                req = copy(rslt)
            if isinstance(rslt, Response):
                raise MiddlewareShortCircuit(response=rslt.to_dict())
        return req

    def _process_options_request(self, request):
        """
        Handle OPTIONS requests for CORS preflight.

        Parameters
        ----------
        request : BaseRequest
            The incoming request object.

        Returns
        -------
        Response
            Response with CORS headers.
        """
        return Response(
            code=200,
            headers=self.cors_headers
        )

    def _config_logging(self):
        """
        Configure logging for the API instance.

        Returns
        -------
        logging.Logger
            Configured logger.
            
            revisar()...
        """
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
        """
        Get the current debug mode status.

        Returns
        -------
        bool
            Boolean indicating if debug mode is enabled.
        """
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        """
        Set the debug mode status.

        Parameters
        ----------
        value : bool
            Boolean to enable or disable debug mode.
        """
        self._debug = value
        self.log.setLevel(logging.DEBUG if self._debug else logging.INFO)
