==============================
Streams Tutorial using mango_pycore / DynamoDB Products Inventory Example
==============================

In this tutorial, we'll guide you through a **practical example** of using the `Stream` class from the `mango_pycore` library in a real-world scenario. We'll create a DynamoDB table to store products in an inventory system and trigger actions when products are added, updated, or deleted.

We'll walk through:

- Setting up a DynamoDB table named `Products`.
- Enabling DynamoDB Streams to capture changes.
- Using the `Stream` class to register handlers for `INSERT`, `MODIFY`, and `REMOVE` events.
- Simulating these events and testing them locally.
- Including all technical steps required to run the tutorial on any computer.


Prerequisites
-------------
Before you begin, ensure you have the following:

- **AWS Account**: Access to an AWS account to set up DynamoDB.
- **AWS CLI**: Installed and configured with your AWS credentials.
- **Python Environment**: Python 3.8+ installed.
- **AWS SAM CLI**: Installed for testing and deploying Lambda functions locally.
- **Docker(Running)**: Required for local AWS SAM testing.
- **mango-pycore Library**: Installed via pip.

Install `mango-pycore` using pip:

.. code-block:: bash

    pip install mango-pycore


Step 1: Create a DynamoDB Table
-------------------------------
First, we create a DynamoDB table named `Products` to store product information. The table will have the following structure:

- **Primary Key (PK):** `product_id` (string)
- **Sort Key (SK):** `category` (string)

Open your terminal and run the following AWS CLI command:

.. code-block:: bash

    aws dynamodb create-table \
        --table-name Products \
        --attribute-definitions AttributeName=product_id,AttributeType=S AttributeName=category,AttributeType=S \
        --key-schema AttributeName=product_id,KeyType=HASH AttributeName=category,KeyType=RANGE \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

This command creates the **Products** table with the specified primary key (`product_id`) and sort key (`category`).


Step 2: Enable DynamoDB Streams
-------------------------------
Next, enable DynamoDB Streams on the table to capture changes (INSERT, MODIFY, REMOVE events).

Run the following AWS CLI command:

.. code-block:: bash

    aws dynamodb update-table \
        --table-name Products \
        --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES

This will capture both the old and new values when a record is modified or removed.


Step 3: Set Up the Stream Handler
---------------------------------
We'll now set up the `Stream` class to handle DynamoDB stream events for product insertion, updates, and deletions.

#. **Create a project directory** and navigate into it:

   .. code-block:: bash

       mkdir dynamodb-streams-tutorial
       cd dynamodb-streams-tutorial

#. **Initialize a new AWS SAM application**:

   .. code-block:: bash

       sam init

   - Choose **1 - AWS Quick Start Templates**.
   - Choose **1 - Zip**.
   - Choose **3 - python3.8**.
   - Use the default name or provide one.
   - Choose **1 - Hello World Example**.

#. **Navigate to the application directory**:

   .. code-block:: bash

       cd sam-app

#. **Install the `mango-pycore` library** in the Lambda function directory:

   .. code-block:: bash

       cd hello_world
       pip install mango-pycore -t .

#. **Replace the existing `app.py`** file with the following code:

   .. code-block:: python

       import json
       from mango_pycore.stream.dynamo import Stream
       from mango_pycore.tools.utils import from_dynamodb_to_json
       import logging

       # Initialize Stream
       stream = Stream(pk_name="product_id", sk_name="category", name="InventoryStreamHandler")

       # Handler for new product (INSERT)
       @stream.register(p_key="123", actions=["INSERT"])
       def handle_insert(old_data, new_data, table_name):
           print(f"New product added: {new_data}")

       # Handler for updating product (MODIFY)
       @stream.register(p_key="123", actions=["MODIFY"])
       def handle_modify(old_data, new_data, table_name):
           print(f"Product updated. Old: {old_data}, New: {new_data}")

       # Handler for removing product (REMOVE)
       @stream.register(p_key="123", actions=["REMOVE"])
       def handle_remove(old_data, new_data, table_name):
           print(f"Product removed: {old_data}")

       # Lambda function to process stream events
       def lambda_handler(event, context):
           stream(event, context)

#. **Update the `template.yaml`** file to configure the Lambda function for DynamoDB Streams:

   Replace the existing function configuration with the following:

   .. code-block:: yaml

       AWSTemplateFormatVersion: '2010-09-09'
       Transform: AWS::Serverless-2016-10-31
       Description: >
         dynamodb-streams-tutorial

       Resources:
         InventoryStreamFunction:
           Type: AWS::Serverless::Function
           Properties:
             CodeUri: hello_world/
             Handler: app.lambda_handler
             Runtime: python3.8
             Events:
               DynamoDBStream:
                 Type: DynamoDB
                 Properties:
                   Stream: arn:aws:dynamodb:us-east-1:123456789012:table/Products/stream/2023-01-01T00:00:00.000
                   StartingPosition: TRIM_HORIZON

   **Note**: Replace the `Stream` ARN with the actual ARN of your DynamoDB table stream. You can find it by running:

   .. code-block:: bash

       aws dynamodb describe-table --table-name Products --query "Table.LatestStreamArn" --output text


Step 4: Create Simulated Events
-------------------------------
Now, let's create simulated DynamoDB stream events to test the `INSERT`, `MODIFY`, and `REMOVE` operations.

### Simulating an `INSERT` Event

#. **Create a file** named `insert_event.json` in the root of your project directory.

#. **Add the following JSON content**:

   .. code-block:: json

       {
           "Records": [
               {
                   "eventID": "1",
                   "eventName": "INSERT",
                   "eventVersion": "1.1",
                   "eventSource": "aws:dynamodb",
                   "awsRegion": "us-east-1",
                   "dynamodb": {
                       "Keys": {
                           "product_id": {"S": "123"},
                           "category": {"S": "Electronics"}
                       },
                       "NewImage": {
                           "product_id": {"S": "123"},
                           "category": {"S": "Electronics"},
                           "name": {"S": "Smartphone"},
                           "price": {"N": "999"},
                           "quantity": {"N": "50"}
                       },
                       "StreamViewType": "NEW_AND_OLD_IMAGES",
                       "SequenceNumber": "111",
                       "SizeBytes": 26
                   },
                   "eventSourceARN": "arn:aws:dynamodb:us-east-1:123456789012:table/Products/stream/2023-01-01T00:00:00.000"
               }
           ]
       }

### Simulating a `MODIFY` Event

#. **Create a file** named `modify_event.json`.

#. **Add the following JSON content**:

   .. code-block:: json

       {
           "Records": [
               {
                   "eventID": "2",
                   "eventName": "MODIFY",
                   "eventVersion": "1.1",
                   "eventSource": "aws:dynamodb",
                   "awsRegion": "us-east-1",
                   "dynamodb": {
                       "Keys": {
                           "product_id": {"S": "123"},
                           "category": {"S": "Electronics"}
                       },
                       "OldImage": {
                           "product_id": {"S": "123"},
                           "category": {"S": "Electronics"},
                           "name": {"S": "Smartphone"},
                           "price": {"N": "999"},
                           "quantity": {"N": "50"}
                       },
                       "NewImage": {
                           "product_id": {"S": "123"},
                           "category": {"S": "Electronics"},
                           "name": {"S": "Smartphone Pro"},
                           "price": {"N": "1299"},
                           "quantity": {"N": "30"}
                       },
                       "StreamViewType": "NEW_AND_OLD_IMAGES",
                       "SequenceNumber": "222",
                       "SizeBytes": 59
                   },
                   "eventSourceARN": "arn:aws:dynamodb:us-east-1:123456789012:table/Products/stream/2023-01-01T00:00:00.000"
               }
           ]
       }

### Simulating a `REMOVE` Event

#. **Create a file** named `remove_event.json`.

#. **Add the following JSON content**:

   .. code-block:: json

       {
           "Records": [
               {
                   "eventID": "3",
                   "eventName": "REMOVE",
                   "eventVersion": "1.1",
                   "eventSource": "aws:dynamodb",
                   "awsRegion": "us-east-1",
                   "dynamodb": {
                       "Keys": {
                           "product_id": {"S": "123"},
                           "category": {"S": "Electronics"}
                       },
                       "OldImage": {
                           "product_id": {"S": "123"},
                           "category": {"S": "Electronics"},
                           "name": {"S": "Smartphone Pro"},
                           "price": {"N": "1299"},
                           "quantity": {"N": "30"}
                       },
                       "StreamViewType": "NEW_AND_OLD_IMAGES",
                       "SequenceNumber": "333",
                       "SizeBytes": 38
                   },
                   "eventSourceARN": "arn:aws:dynamodb:us-east-1:123456789012:table/Products/stream/2023-01-01T00:00:00.000"
               }
           ]
       }


Step 5: Build and Test Locally
------------------------------
Now we'll build the SAM application and test it locally using the simulated events.

#. **Navigate back to the root of your SAM application**:

   .. code-block:: bash

       cd ..

#. **Build the SAM application**:

   .. code-block:: bash

       sam build

#. **Test the function locally with the `INSERT` event**:

   .. code-block:: bash

       sam local invoke InventoryStreamFunction --event insert_event.json

   You should see the following output:

   .. code-block:: bash

       START RequestId: ... Version: $LATEST
       New product added: {'product_id': '123', 'category': 'Electronics', 'name': 'Smartphone', 'price': 999, 'quantity': 50}
       END RequestId: ...
       REPORT RequestId: ... Duration: ... ms Billed Duration: ... ms Memory Size: ... MB Max Memory Used: ... MB

#. **Test the function locally with the `MODIFY` event**:

   .. code-block:: bash

       sam local invoke InventoryStreamFunction --event modify_event.json

   Expected output:

   .. code-block:: bash

       START RequestId: ... Version: $LATEST
       Product updated. Old: {'product_id': '123', 'category': 'Electronics', 'name': 'Smartphone', 'price': 999, 'quantity': 50}, New: {'product_id': '123', 'category': 'Electronics', 'name': 'Smartphone Pro', 'price': 1299, 'quantity': 30}
       END RequestId: ...
       REPORT RequestId: ... Duration: ... ms Billed Duration: ... ms Memory Size: ... MB Max Memory Used: ... MB

#. **Test the function locally with the `REMOVE` event**:

   .. code-block:: bash

       sam local invoke InventoryStreamFunction --event remove_event.json

   Expected output:

   .. code-block:: bash

       START RequestId: ... Version: $LATEST
       Product removed: {'product_id': '123', 'category': 'Electronics', 'name': 'Smartphone Pro', 'price': 1299, 'quantity': 30}
       END RequestId: ...
       REPORT RequestId: ... Duration: ... ms Billed Duration: ... ms Memory Size: ... MB Max Memory Used: ... MB


Step 6: Deploying to AWS (Optional)
-----------------------------------
If you want to deploy your Lambda function to AWS and test it with real DynamoDB events, follow these steps.

#. **Package the SAM application**:

   .. code-block:: bash

       sam package --output-template-file packaged.yaml --s3-bucket your-s3-bucket-name

   Replace `your-s3-bucket-name` with an actual S3 bucket in your AWS account.

#. **Deploy the SAM application**:

   .. code-block:: bash

       sam deploy --template-file packaged.yaml --stack-name dynamodb-streams-tutorial --capabilities CAPABILITY_IAM

#. **Update the DynamoDB Table to Use the Lambda Function**

   After deployment, you need to set up the DynamoDB Streams trigger in AWS to point to your Lambda function.

   - Go to the AWS Lambda console.
   - Find your function (`InventoryStreamFunction`).
   - In the "Configuration" tab, under "Triggers", ensure that the DynamoDB stream from your `Products` table is added.


Conclusion
----------
In this tutorial, we walked through the complete process of:

- Creating a DynamoDB table called **Products**.
- Enabling DynamoDB Streams to track changes.
- Setting up a Python script using the `Stream` class to handle stream events.
- Simulating stream events for `INSERT`, `MODIFY`, and `REMOVE` actions using local test files.
- Building and testing the application locally with AWS SAM CLI.
- (Optional) Deploying the Lambda function to AWS and connecting it to the DynamoDB Streams.

By following these steps, you can set up event-driven processing for DynamoDB tables in your project, automating actions when records are added, updated, or deleted.




