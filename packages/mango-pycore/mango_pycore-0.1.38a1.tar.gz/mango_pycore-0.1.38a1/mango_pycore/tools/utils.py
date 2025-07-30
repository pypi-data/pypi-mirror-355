import os

from boto3.dynamodb.types import TypeDeserializer

def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}

def set_environment_vars(origin, data):
    os.environ["ORIGIN"] = origin
    for key, value in data.items():
        if type(value) == list:
            os.environ[key] = str(value)
        elif type(value) == dict:
            os.environ[key] = str(value)
        else:
            os.environ[key] = str(value)