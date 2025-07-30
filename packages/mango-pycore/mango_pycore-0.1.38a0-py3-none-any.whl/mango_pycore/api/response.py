import decimal
import json

class CustomEncoder(json.JSONEncoder):
    """
    A custom JSON encoder to handle decimal.Decimal objects.

    Methods
    -------
    default(o)
        Override the default method to handle decimal.Decimal objects.
    """

    def default(self, o):
        """
        Override the default method to handle decimal.Decimal objects.

        Parameters
        ----------
        o : object
            The object to encode.

        Returns
        -------
        int or float or object
            The encoded object.
        """
        if isinstance(o, decimal.Decimal):
            if float(o) == int(o):
                return int(o)
            else:
                return float(o)
        return super().default(o)

class Response:
    """
    A class to represent an HTTP response.

    Attributes
    ----------
    headers : dict
        The headers of the response.
    code : int
        The HTTP status code of the response.
    encoded : bool
        Flag to indicate if the response body is Base64 encoded.
    body : object
        The body of the response.

    Methods
    -------
    to_dict()
        Convert the response object to a dictionary.
    """

    def __init__(self, code=200, encoded=False, body=None, headers={}):
        """
        Constructs all the necessary attributes for the Response object.

        Parameters
        ----------
        code : int, optional
            The HTTP status code of the response (default is 200).
        encoded : bool, optional
            Flag to indicate if the response body is Base64 encoded (default is False).
        body : object, optional
            The body of the response (default is None).
        headers : dict, optional
            Additional headers to include in the response (default is an empty dictionary).
        """
        self.headers = {
            "Content-Type": "application/json",
        }
        self.headers.update(headers)
        self.code = code
        self.encoded = encoded
        self.body = body

    def to_dict(self):
        """
        Convert the response object to a dictionary.

        Returns
        -------
        dict
            The response object as a dictionary.
        """
        response = {
            "isBase64Encoded": self.encoded,
            "statusCode": self.code,
            "headers": self.headers,
        }
        if self.body is not None:
            response.update({
                "body": json.dumps(self.body, cls=CustomEncoder)
            })

        return response