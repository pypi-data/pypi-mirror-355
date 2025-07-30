Hello World Tutorial with mango_pycore
======================================

This tutorial will guide you through creating a simple "Hello World" API using the `mango_pycore` library. We will use AWS SAM (Serverless Application Model) to deploy the API on AWS Lambda.

Prerequisites
--------------
Before starting, make sure you have the following tools installed:
- Python 3.8 or later
- AWS SAM CLI
- Docker (for local testing)
- `mango_pycore` library

Step 1: Setting Up Your Project
-------------------------------
Create a new directory for your project and navigate into it. Inside this directory, you will create three essential files: `app.py`, `template.yaml`, and `requirements.txt`.

.. code-block:: bash

    $ mkdir hello-world
    $ cd hello-world
    $ touch app.py template.yaml requirements.txt

Step 2: Creating the Application Code
--------------------------------------
Inside the project folder, create a file named `app.py` with the following content. This file contains the code for your AWS Lambda function.

.. code-block:: python

    from mango_pycore.api.rest_api import RestApi
    from mango_pycore.api.request import RestApiRequest
    from mango_pycore.api.response import Response

    # Create an instance of RestApi
    app = RestApi()
    app.debug = True

    @app.route(path="/", methods=["GET"])
    def hello_world(request: RestApiRequest):
        return Response(
            code=200,
            body={
                "message": "Hello World",
            }
        )

This code defines a REST API with a single route ("/") that responds to GET requests with a "Hello World" message.

Step 3: Creating the SAM Template
----------------------------------
Create a file named `template.yaml` with the following content. This AWS SAM template defines the AWS resources needed to deploy your Lambda function.

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

This template defines:
- **RestApi**: An AWS API Gateway that exposes your Lambda function.
- **HelloWorldFunction**: The AWS Lambda function that will handle API requests.
- **Outputs**: Provides the URL of your API and the ARN of your Lambda function.

Step 4: Defining Dependencies
------------------------------
Create a file named `requirements.txt` with the following content. This file lists the dependencies required by your Lambda function.

.. code-block:: text

    mango-pycore==0.1.3

Step 5: Building and Testing Locally
------------------------------------
To build and test your Lambda function locally, follow these steps:

1. **Build the application:**

   .. code-block:: bash

        $ sam build

2. **Start the API locally:**

   .. code-block:: bash

        $ sam local start-api

   Your API will be available at `http://127.0.0.1:3000`. You can test it by sending a GET request to this URL.

   .. code-block:: bash

        $ http GET http://127.0.0.1:3000/

   You should receive a response with the "Hello World" message.

   .. code-block::

        HTTP/1.1 200 OK
        Access-Control-Allow-Headers: Content-Type, X-Amz-Date, Authorization,X-Api-Key,X-Amz-Security-Token
        Access-Control-Allow-Origin: *
        Access-Control-Max-Age: 600
        Connection: close
        Content-Length: 26
        Content-Type: application/json
        Date: Tue, 03 Sep 2024 17:07:43 GMT
        Server: Werkzeug/3.0.3 Python/3.8.13

        {
         "message": "Hello World"
        }

Conclusion
----------
Congratulations! You've successfully created and deployed a simple "Hello World" API using `mango_pycore` and AWS SAM. You can now expand this basic example to build more complex serverless applications.
