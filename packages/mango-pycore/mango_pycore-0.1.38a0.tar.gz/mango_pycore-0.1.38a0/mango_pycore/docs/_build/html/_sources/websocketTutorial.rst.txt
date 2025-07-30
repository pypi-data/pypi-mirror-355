Websocket Tutorial 
====================================

This tutorial will guide you through the process of creating and sending messages from the `mango_pycore` library to the WebSocket server.

Prerequisites
-------------

Before starting, make sure you have the following tools installed:

- Python 3.8 or later
- AWS SAM CLI
- Docker (for local testing)
- `mango_pycore` library

Step 1: Imports
---------------

Create a Python file called `send_message.py`. This file will contain the code to send messages to the WebSocket server. At the top of the file, include the following imports:

.. code-block:: python

    from mango_pycore.api.websocket.client import WebsocketClient
    import json

We are importing `json` to convert the messages to JSON format. The `mango_pycore` library provides a `WebsocketClient` class that we will use to connect to the WebSocket server.

Step 2: Creating the WebSocket Client
-------------------------------------

To create the WebSocket client, we need to provide the server URL. Here is an example of how to create the WebSocket client:

.. code-block:: python

    websocket = WebsocketClient(server="wss://mango-api.com/v1")

`websocket` is the instance of the class we will be using. `server` is the URL of the WebSocket server we will be connecting to.

Step 3: Creating the Message
----------------------------

Let's take a look at the following example:

.. code-block:: python

    websocket.send(
        channel="helloworld",
        message=json.dumps(
            {"company": "Mango Soft Inc.", 
             "country": "United States",
             "state": "Florida",
             "city": "Miami"})
    )

We are going to use the `send` method of the `websocket` instance to send a message to the server. This method requires two variables:

1. The `channel` variable is the name of the channel we are going to send the message to.

   .. code-block:: python

       channel = "helloworld"

2. The `message` variable is the message we are going to send to the server. We are using the `json.dumps` method to convert the message to JSON format.

   .. code-block:: python

       message = json.dumps(
           {"company": "Mango Soft Inc.", 
            "country": "United States",
            "state": "Florida",
            "city": "Miami"})

Step 4: Testing the WebSocket Client
------------------------------------

The final code should look like this:

.. code-block:: python

    from mango_pycore.api.websocket.client import WebsocketClient
    import json

    websocket = WebsocketClient(server="wss://mango-api.com/v1")

    websocket.send(
        channel="helloworld",
        message=json.dumps(
            {"company": "Mango Soft Inc.", 
             "country": "United States",
             "state": "Florida",
             "city": "Miami"})
    )

To test the WebSocket client, we are going to use POSTMAN. POSTMAN allows us to connect to WebSocket servers. We'll need to connect to the same server used in the code.

.. code-block:: bash

    wss://mango-api.com/v1?channel=helloworld

NOTICE that we are using the same channel as in the code.

After connecting to the server, run the `send_message.py` file to send the message to the server.

.. code-block:: bash

    $ python send_message.py

You should see the message in the POSTMAN console.

Step 5: Testing and Format
--------------------------

Since we used the `json.dumps` method, the message will appear in text format.

.. code-block:: bash

    {\"company\": \"Mango Soft Inc.\", \"country\": \"United States\", \"state\": \"Florida\", \"city\": \"Miami\"}

The `mango_pycore` WebSocket client allows you to send messages in the format you need. You can use this to send messages to the WebSocket server and receive responses from the server.

.. code-block:: python

    websocket.send(
        channel="helloworld",
        message={
            "company": "Mango Soft Inc.", 
            "country": "United States",
            "state": "Florida",
            "city": "Miami"}
    )

This format will allow you to see the message in JSON format.

.. code-block:: bash

    {"company": "Mango Soft Inc.", "country": "United States", "state": "Florida", "city": "Miami"}

Conclusion
----------

1. We need to import the `WebsocketClient` class from the `mango_pycore` library to create a WebSocket client.
2. Make an instance of the class specifying the server URL.
3. Call the `send` method of the `websocket` instance to send messages to the server.
4. The `send` method should have the `channel` and `message` variables to send the message to the server.

The front end (simulated by POSTMAN) will be actively listening, and when the message is sent, it will be displayed in the console.

In this tutorial, we learned how to create a WebSocket client using the `mango_pycore` library. We also learned how to send messages to the WebSocket server in different formats. You can use this knowledge to create your own WebSocket clients and send messages to the server.