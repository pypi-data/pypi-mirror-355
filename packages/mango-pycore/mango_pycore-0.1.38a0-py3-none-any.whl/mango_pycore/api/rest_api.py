import json
import traceback

from mango_pycore.api.base_api import Api
from mango_pycore.api.request import RestApiRequest
from mango_pycore.api.response import Response
from mango_pycore.api.exceptions import BadRequest, MiddlewareShortCircuit

# Default CORS headers used for preflight requests and responses
default_cors_headers = {
    "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Max-Age": 600,
    "Content-Type": "application/json"
}

class RestApi(Api):
    """
    A class to represent a REST API, extending the base Api class.

    Methods
    -------
    __call__(event, context, *args, **kwargs)
        Handle the incoming event and context, process the request, and return a response.
    """

    def __init__(self, name="SAM-API", cors_headers=None, cors_function=None):
        """
        Constructs all the necessary attributes for the RestApi object.

        Parameters
        ----------
        name : str, optional
            The name of the API (default is "SAM-API").
        cors_headers : dict, optional
            The CORS headers to be used (default is None, which uses default_cors_headers).
        cors_function : function, optional
            The function to handle CORS preflight requests (default is None, which uses _process_options_request).
        """
        super().__init__(name=name, cors_headers=cors_headers, cors_function=cors_function)

    def __call__(self, event, context, *args, **kwargs):
        """
        Handle the incoming event and context, process the request, and return a response.

        Parameters
        ----------
        event : dict
            The event data from the API Gateway.
        context : object
            The context object provided by the AWS Lambda runtime.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        dict
            The response object to be returned to the API Gateway.
        """
        try:
            request = self._process_middlewares(RestApiRequest(event=event, app=self, debug=self.debug)) if \
            event['requestContext']['httpMethod'].lower() != "options" else RestApiRequest(event=event, app=self,
                                                                                           debug=self.debug)
            self.log.debug(event)

            route_key = request.route_key

            function = self._resources[route_key]
            response = function(request)

            base_headers = self.cors_headers.copy()

            if isinstance(response, Response):
                rslt = response.to_dict()
                rslt_headers = rslt.get('headers', {})
                base_headers.update(rslt_headers)
                rslt['headers'] = base_headers
                return rslt

            response_headers = response.get('headers', {})
            base_headers.update(response_headers)
            response['headers'] = base_headers
            return response

        except MiddlewareShortCircuit as e:
            return e.response

        except BadRequest as e:
            return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps({
                    "error": e.message
                })
            }
        except Exception as e:
            self.log.error(str(e))
            debug_error = traceback.format_exc()
            return {
                "isBase64Encoded": False,
                "statusCode": 500,
                "body": json.dumps({
                    "error": debug_error if self.debug else "Internal Server Error"
                })
            }