RestApi Tutorial
===================================

This tutorial will guide you through creating a REST API using the `mango_pycore` library.

This tutorial is the second part of the Hello World tutorial.

Prerequisites
-------------

Before starting, make sure you have the following tools installed:

- Python 3.8 or later
- AWS SAM CLI
- Docker (for local testing)
- `mango_pycore` library

Step 2: Modifying the URL GET Parameters
----------------------------------------

Inside the `app.py` file we previously created, we will add the following function:

.. code-block:: python

    from mango_pycore.api.rest_api import RestApi
    from mango_pycore.api.request import RestApiRequest
    from mango_pycore.api.response import Response

    app = RestApi()
    app.debug = True

    CIUDADES = {
        'Bogota': 'Cundinamarca',
        'Medellin': 'Antioquia',
    }

    @app.route(path="/", methods=["GET"])
    def hello_world(request: RestApiRequest):
        return Response(
            code=200,
            body={"message": "Hello World"}
        )

    @app.route(path='/ciudades/{ciudad}', methods=['GET'])
    def depto_ciudad(request: RestApiRequest):
        ciudad = request.path_parameters.get('ciudad')
        departamento = CIUDADES.get(ciudad)
        return Response(
            code=200,
            body={'departamento': departamento}
        )

NOTICE: We added the `CIUDADES` dict and the `depto_ciudad` function to the `app.py` file. In the `depto_ciudad` function, we are using the `path_parameters` attribute of the `request` object to get the value of the `ciudad` parameter in the URL.

Step 3: Modifying the SAM Template
----------------------------------

Inside the file named `template.yaml` we previously created, we will add the following content:

.. code-block:: yaml

    AWSTemplateFormatVersion: '2010-09-09'
    Transform: AWS::Serverless-2016-10-31
    Description: >
      MANGO_Boilerplate_BackEnd Stack
    Globals:
      Function:
        Timeout: 30
        MemorySize: 512
    Resources:
      RestApi:
        Type: AWS::Serverless::Api
        Properties:
          StageName: v1
      HelloWorldFunction:
        Type: AWS::Serverless::Function
        Properties:
          CodeUri: .
          Handler: app.app
          Runtime: python3.8
          Architectures:
            - x86_64
          Events:
            optionsCollection:
              Type: Api
              Properties:
                RestApiId: !Ref RestApi
                Method: options
                Path: /{proxy+}
            helloWorld:
              Type: Api
              Properties:
                RestApiId: !Ref RestApi
                Method: get
                Path: /
            depto_ciudad:
              Type: Api
              Properties:
                RestApiId: !Ref RestApi
                Method: get
                Path: /ciudades/{ciudad}
    Outputs:
      UrlApi:
        Description: URL of your API
        Value:
          Fn::Sub: 'http://127.0.0.1:3000/v1'
      HelloWorldFunction:
        Description: "Hello World Lambda Function ARN"
        Value: !GetAtt HelloWorldFunction.Arn
      HelloWorldFunctionIamRole:
        Description: "Implicit IAM Role created for Hello World function"
        Value: !GetAtt HelloWorldFunction.Arn

NOTICE: We added the `depto_ciudad` event to the `HelloWorldFunction` resource. This event will trigger the `depto_ciudad` function when a GET request is made to the `/ciudades/{ciudad}` URL.

Remember to rebuild the application using the `sam build` command and start the API using the `sam local start-api` command.

This template defines:

- **RestApi**: An AWS API Gateway that exposes your Lambda function.
- **HelloWorldFunction**: The AWS Lambda function that will handle API requests.
- **Outputs**: Provides the URL of your API and the ARN of your Lambda function.

Step 4: Testing the new URL Parameters
--------------------------------------

Build your application using the following command:

.. code-block:: bash

    $ sam build
    $ sam local start-api

Your API will be available at `http://127.0.0.1:3000`.

Send a GET request with the depto_ciudad parameter to the URL:

.. code-block:: bash

    $ http GET localhost:3000/ciudades/Medellin
    HTTP/1.1 200 OK

    "departamento": "Antioquia"

    $ http GET localhost:3000/ciudades/Bogota
    HTTP/1.1 200 OK

    "departamento": "Cundinamarca"

PUT request
-----------

Our examples have only allowed GET requests. It’s possible to support additional HTTP methods with mango-pycore. Here’s an example of a view function that supports PUT:

.. code-block:: python

    @app.route(path='/ciudades/{ciudad}', methods=['PUT'])
    def update_ciudad(request: RestApiRequest):
        ciudad = request.path_parameters.get('ciudad')
        # Parse the request body as JSON
        data = json.loads(request.body)
        departamento = data.get('departamento')
        # Update the CIUDADES dictionary
        CIUDADES[ciudad] = departamento
        return Response(
            code=200,
            body={"ciudades": CIUDADES}
        )

Remember to add the event to the template.yaml file, to rebuild the application using the `sam build` command and start the API using the `sam local start-api` command.

To Test it RUN the following command in your terminal:

.. code-block:: bash

    http PUT localhost:3000/ciudades/Bogota departamento="Santander"

You should get the response:

.. code-block:: bash

    HTTP/1.1 200 OK

    "ciudades": {
        "Bogota": "Santander",
        "Medellin": "Antioquia"
    }

NOTICE that we are using the PUT method to update the value of the `departamento` key in the `CIUDADES` dictionary. We are using attributes of the `request` object to get the `path_parameters` and the `body` of the request. This is done through the RestApiRequest object from mango-pycore.

POST request
------------

Here’s an example of a view function that supports POST:

.. code-block:: python

    @app.route(path='/ciudades', methods=['POST'])
    def create_ciudad(request: RestApiRequest):
        # Parse the request body as JSON
        data = json.loads(request.body)
        ciudad = data.get('ciudad')
        departamento = data.get('departamento')
        # Add the new ciudad to the CIUDADES dictionary
        CIUDADES[ciudad] = departamento
        return Response(
            code=201,  # 201 Created
            body={"ciudades": CIUDADES}
        )

Remember to add the event to the template.yaml file, to rebuild the application using the `sam build` command and start the API using the `sam local start-api` command.

To Test it RUN the following command in your terminal:

.. code-block:: bash

    http POST localhost:3000/ciudades ciudad="Cartagena" departamento="Bolivar"

You should get the response:

.. code-block:: bash

    HTTP/1.1 201 Created

    "ciudades": {
        "Bogota": "Cundinamarca",
        "Medellin": "Antioquia",
        "Cartagena": "Bolivar"
    }

NOTICE that we are using the POST method to add a new key-value pair to the `CIUDADES` dictionary.

DELETE request
--------------

Here’s an example of a view function that supports DELETE:

.. code-block:: python

    @app.route(path='/ciudades/{ciudad}', methods=['DELETE'])
    def delete_ciudad(request: RestApiRequest):
        ciudad = request.path_parameters.get('ciudad')
        # Delete the ciudad from the CIUDADES dictionary
        del CIUDADES[ciudad]
        return Response(
            code=200,
            body={"ciudades": CIUDADES}
        )

Remember to add the event to the template.yaml file, to rebuild the application using the `sam build` command and start the API using the `sam local start-api` command.

To Test it RUN the following command in your terminal:

.. code-block:: bash

    http DELETE localhost:3000/ciudades/Bogota

You should get the response:

.. code-block:: bash

    HTTP/1.1 200 OK

    "ciudades": {
        "Medellin": "Antioquia"
    }

REQUEST
-------

The `request.path_parameters` and the `request.body` are part of the RestApiRequest object from mango-pycore which also has the following properties:

.. code-block:: python

    self.headers = event['headers']
    self.method = event['requestContext']['httpMethod']
    self.path = event['path']
    self.timestamp = event['requestContext']['requestTimeEpoch']
    self.date = datetime.datetime.utcfromtimestamp(self.timestamp/1000)
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

This is further explained in the `mango_pycore` documentation.

Conclusion
----------

Congratulations! You've successfully created and deployed a Rest API using `mango_pycore` and AWS SAM. You can now expand this basic example to build more complex serverless applications.