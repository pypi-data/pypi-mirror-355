class BadRequest(Exception):
    """
    Exception raised for a bad request format.

    Attributes:
        message (str): Explanation of the error.
    """

    def __init__(self, message="Bad request format"):
        """
        Initializes BadRequest with an optional error message.

        Args:
            message (str): Custom error message. Defaults to "Bad request format".
        """
        self.message = message
        super().__init__(self.message)


class MiddlewareShortCircuit(Exception):
    """
    Exception raised to interrupt middleware processing.

    Attributes:
        response (Any): The response object or value to be returned directly.
    """

    def __init__(self, response):
        """
        Initializes MiddlewareShortCircuit with a response to be returned.

        Args:
            response (Any): The response to be returned in case of middleware interruption.
        """
        self.response = response
        super().__init__('')
