Using Environment Data in mango_pycoree
============================================================

In this tutorial, we will demonstrate how to use the environment data functionalities provided by `mango_pycore` in a realistic application. We will focus on utilizing the `EnvironmentDataService` and `AuditService` to manage configuration data and create audit logs, without delving into the implementation details of the modules.

Prerequisites
--------------

Before starting, ensure you have the following:

- **Python 3.8** or later
- **AWS SAM CLI** (if deploying to AWS Lambda)
- **Docker** (for local testing)
- **mango_pycore** library installed
- **AWS Credentials** configured (if using AWS services)
- Basic understanding of previous `mango_pycore` tutorials

Project Overview
-----------------

We will build a serverless application that:

- Loads environment-specific configuration data.
- Performs operations based on this configuration.
- Creates audit logs of user actions.

This application will simulate a simple API that returns configuration settings and logs actions using the services provided by `mango_pycore`.

Setting Up the Project
-----------------------

Create a new directory for your project and navigate into it:

.. code-block:: bash

    $ mkdir mango_env_app
    $ cd mango_env_app

Create the essential files:

.. code-block:: bash

    $ touch app.py template.yaml requirements.txt

Install the required dependencies by adding them to your `requirements.txt` file:

.. code-block:: text

    mango-pycore==0.1.3
    requests
    boto3
    pycryptodome
    rsa

Then, install the dependencies:

.. code-block:: bash

    $ pip install -r requirements.txt

Creating the Application Code
------------------------------

### 1. Import Necessary Modules

In your `app.py`, import the required modules from `mango_pycore` and other libraries:

.. code-block:: python

    # app.py
    from mango_pycore.api.rest_api import RestApi
    from mango_pycore.api.request import RestApiRequest
    from mango_pycore.api.response import Response
    from mango_pycore.environment_data.services.environment_data_service import EnvironmentDataService
    from mango_pycore.environment_data.services.audit_service import AuditService

    import os
    import logging

### 2. Initialize the Application and Services

Initialize the `RestApi` application and the environment data services:

.. code-block:: python

    app = RestApi()
    app.debug = True

    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

 