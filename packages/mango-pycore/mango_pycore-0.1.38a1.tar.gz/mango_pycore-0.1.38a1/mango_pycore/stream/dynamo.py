import logging
import traceback

from ..tools.utils import from_dynamodb_to_json

class Stream:
    """
    A class to handle DynamoDB stream events.

    Attributes
    ----------
    pk_name : str
        The primary key name for the DynamoDB table.
    sk_name : str
        The sort key name for the DynamoDB table.
    name : str
        The name used for logging.
    _resources : dict
        A dictionary to store registered actions.
    _debug : bool
        A flag to set the logging level to DEBUG.
    log : logging.Logger
        The logger instance for logging events.
    """

    def __init__(self, pk_name, sk_name, name="Dynamo"):
        """
        Initialize the Stream object with primary and sort key names.

        Parameters
        ----------
        pk_name : str
            The primary key name.
        sk_name : str
            The sort key name.
        name : str, optional
            The name used for logging (default is "Dynamo").
        """
        self._resources = {}
        self.pk_name = pk_name
        self.sk_name = sk_name
        self.name = name
        self._debug = False
        self.log = self._config_logging()

    def __call__(self, event, context, *args, **kwargs):
        """
        Process the DynamoDB stream event.

        Parameters
        ----------
        event : dict
            The event data from the DynamoDB stream.
        context : object
            The context in which the event is executed.
        *args : tuple
            Additional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        bool
            True if the event is processed successfully.
        """
        self.rawEvent = event
        self.rawContext = context

        self.log.debug(event)
        try:
            # Ensure the event contains 'Records'
            assert 'Records' in event.keys(), "Key 'Records' is missing in stream"
            for record in event["Records"]:
                # Ensure each record contains 'eventName' and 'eventSourceARN'
                assert 'eventName' in record.keys(), "Key 'eventName' is missing in stream"
                action = record["eventName"]
                assert 'eventSourceARN' in record.keys(), "Key 'eventSourceARN' is missing in stream"
                arn = record['eventSourceARN']
                table_name = arn.split("/")[1]

                pk = ""
                db_data_old = None
                db_data_new = None
                # Handle INSERT action
                if action == "INSERT":
                    self.action = "INSERT"
                    db_data_new = from_dynamodb_to_json(record["dynamodb"]["NewImage"])
                    db_data_old = None
                    assert self.pk_name in db_data_new.keys(), f"Key {self.pk_name} is missing in data stream"
                    pk = db_data_new[self.pk_name]
                # Handle MODIFY action
                if action == "MODIFY":
                    self.action = "MODIFY"
                    db_data_new = from_dynamodb_to_json(record["dynamodb"]["NewImage"])
                    db_data_old = from_dynamodb_to_json(record["dynamodb"]["OldImage"])
                    assert self.pk_name in db_data_new.keys(), f"Key {self.pk_name} is missing in data stream"
                    pk = db_data_new[self.pk_name]
                # Handle REMOVE action
                if action == "REMOVE":
                    self.action = "REMOVE"
                    db_data_new = None
                    db_data_old = from_dynamodb_to_json(record["dynamodb"]["OldImage"])
                    assert self.pk_name in db_data_old.keys(), f"Key {self.pk_name} is missing in data stream"
                    pk = db_data_old[self.pk_name]

                key = f"{action} {pk}"
                if key in self._resources.keys():
                    # Call the registered function for the action
                    self._resources[key](db_data_old, db_data_new, table_name)
                else:
                    self.log.debug(f"No handler was found for key '{key}'")
            return True

        except AssertionError as e:
            self.log.debug(traceback.format_exc())
            self.log.critical(str(e))
            exit(0)
        except IndexError as e:
            self.log.debug(traceback.format_exc())
            self.log.critical(str(e))
            exit(0)

    def register(self, p_key, actions: list):
        """
        Decorator to register a function to handle specific actions.

        Parameters
        ----------
        p_key : str
            The primary key for which the actions are registered.
        actions : list
            A list of actions to register (e.g., ['INSERT', 'MODIFY', 'REMOVE']).
        
        Returns
        -------
        function
            The inner function to register the actions.
        """
        def inner_register(function):
            for action in actions:
                self._register_actions(action, p_key, function)
        return inner_register

    def _register_actions(self, action, p_key, function):
        """
        Register a function for a specific action and primary key.

        Parameters
        ----------
        action : str
            The action to register (e.g., 'INSERT', 'MODIFY', 'REMOVE').
        p_key : str
            The primary key for which the action is registered.
        function : function
            The function to handle the action.
        """
        if action in ['INSERT', 'MODIFY', "REMOVE"]:
            key = f"{action} {p_key}"
            if key in self._resources.keys():
                self.log.error(f"Key '{key}' already registered and will be replaced by last function used")
            self._resources[key] = function

    def _config_logging(self):
        """
        Configure the logging for the Stream class.

        Returns
        -------
        logging.Logger
            The configured logger instance.
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
        Get the debug mode status.

        Returns
        -------
        bool
            True if debug mode is enabled, False otherwise.
        """
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        """
        Set the debug mode.

        Parameters
        ----------
        value : bool
            True to enable debug mode, False to disable.
        """
        self._debug = value
        self.log.setLevel(logging.DEBUG if self._debug else logging.INFO)