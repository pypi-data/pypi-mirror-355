import base64
import datetime
import traceback
from typing import Union

from mango_pycore.api.exceptions import BadRequest
from mango_pycore.objects.user import User

class BaseRequest:
    """
    Base class for handling API requests.
    """
    def __init__(self):
        pass

class RestApiRequest(BaseRequest):
    """
    Handles REST API requests from API Gateway version 1.
    """
    def __init__(self, event: dict, app: 'RestApi', debug=False):
        """
        Initializes a RestApiRequest instance.

        :param event: The event data from API Gateway.
        :param app: The application instance.
        :param debug: Flag to enable debug mode.
        """
        super().__init__()
        self.raw_event = event
        self.debug = debug
        self.app = app
        self._process_api_gateway_request_v1(event)

    def _process_api_gateway_request_v1(self, event):
        """
        Processes the API Gateway v1 request event.

        :param event: The event data from API Gateway.
        """
        try:
            # Required Data
            self.headers = event['headers']
            self.method = event['requestContext']['httpMethod']
            self.path = event['path']
            self.timestamp = event['requestContext']['requestTimeEpoch']
            self.date = datetime.datetime.utcfromtimestamp(self.timestamp / 1000)
            self.route_key = f"{self.method} {event['requestContext']['resourcePath']}"
            self.stage = event['requestContext']['stage']

            # Conditional Data
            self.api_id = event['requestContext'].get('apiId')
            self.request_id = event['requestContext'].get('requestId')
            self.cookies = event.get('cookies')
            self.body = event.get('body', {}) if event.get('body', {}) else '{}'
            self.is_base_64_encoded = event.get('isBase64Encoded')
            self.path_parameters = event.get('pathParameters', {})
            self.query_string = event.get('queryStringParameters', {}) if event.get('queryStringParameters') else {}
            self.protocol = event['requestContext'].get('protocol')
            self.source_ip = event['requestContext']['identity'].get('sourceIp')
            self.host = event['requestContext'].get('domainName')

            # Extra Data
            self.user: Union[User, None] = None
        except KeyError:
            e = "Bad request from api gateway v1"
            if self.debug:
                e = traceback.format_exc()
            raise BadRequest(e)

class HttpApiRequest(BaseRequest):
    """
    Handles HTTP API requests from API Gateway version 2.
    """
    def __init__(self, event: dict, app=None, debug=False):
        """
        Initializes an HttpApiRequest instance.

        :param event: The event data from API Gateway.
        :param app: The application instance (optional).
        :param debug: Flag to enable debug mode.
        """
        super().__init__()
        self.raw_event = event
        self.debug = debug
        self.app = app
        self._process_api_gateway_request_v2(event)

    def _process_api_gateway_request_v2(self, event):
        """
        Processes the API Gateway v2 request event.

        :param event: The event data from API Gateway.
        """
        try:
            # Required data
            self.headers = event['headers']
            self.method = event['requestContext']['http']['method']
            self.path = event['requestContext']['http']['path']
            self.timestamp = event['requestContext']['timeEpoch']
            self.date = datetime.datetime.utcfromtimestamp(self.timestamp / 1000)
            self.route_key = event['routeKey']
            self.stage = event['requestContext']['stage']

            # Conditional data
            self.api_id = event['requestContext'].get('apiId')
            self.request_id = event['requestContext'].get('requestId')
            self.body = event.get('body', {}) if event.get('body', {}) else '{}'
            self.cookies = event.get('cookies')
            self.is_base_64_encoded = event.get('isBase64Encoded')
            self.path_parameters = event.get('pathParameters', {})
            self.query_string = event.get('queryStringParameters', {}) if event.get('queryStringParameters') else {}
            self.protocol = event['requestContext']['http'].get('protocol')
            self.source_ip = event['requestContext']['http'].get('sourceIp')
            self.host = event['requestContext'].get('domainName')

            # Extra Data
            self.user: Union[User, None] = None
        except KeyError:
            e = "Bad request from api gateway v2"
            if self.debug:
                e = traceback.format_exc()
            raise BadRequest(e)

class WebsocketApiRequest:
    """
    Handles WebSocket API requests.
    """
    def __init__(self, event: dict, debug=False):
        """
        Initializes a WebsocketApiRequest instance.

        :param event: The event data from API Gateway.
        :param debug: Flag to enable debug mode.
        """
        self.raw_event = event
        self.debug = debug
        self._process_api_websocket_request(event)

    def _process_api_websocket_request(self, event):
        """
        Processes the WebSocket API request event.

        :param event: The event data from API Gateway.
        """
        try:
            # Required Data
            self.route_key = event["requestContext"]["routeKey"]
            self.source_ip = event["requestContext"]["identity"]["sourceIp"]
            self.stage = event["requestContext"]["stage"]
            self.message_direction = event["requestContext"]["messageDirection"]
            self.event_type = event["requestContext"]["eventType"]
            self.request_id = event["requestContext"]["requestId"]
            self.connection_id = event["requestContext"]["connectionId"]
            self.domain_name = event["requestContext"]["domainName"]
            self.is_encoded = event["isBase64Encoded"]
            self.body = self._extract_body(self.is_encoded, event["body"]) if "body" in event.keys() else {}
            self.query_params = event.get("queryStringParameters", {})

        except KeyError:
            e = "Bad request from api gateway websocket"
            if self.debug:
                e = traceback.format_exc()
            raise BadRequest(e)

    def _extract_body(self, encoded, body):
        """
        Extracts the body from the request, decoding if necessary.

        :param encoded: Flag indicating if the body is base64 encoded.
        :param body: The body of the request.
        :return: Decoded body if encoded, otherwise the original body.
        """
        if encoded:
            data = base64.b64decode(body)
            return data
        return body