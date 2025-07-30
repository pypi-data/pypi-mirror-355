import json
import logging
import traceback

import boto3

class S3Environment:
    def __init__(self, bucket, key, role=None, log=logging):
        self._bucket = bucket
        self._key = key
        self._role = role
        self._log = log
        self._s3_client = self._get_s3_client()

    def get_backend_data(self, origin):
        try:
            obj = self._s3_client.get_object(
                Bucket=self._bucket,
                Key=self._key
            )
            obj_data = obj['Body'].read().decode("utf-8")
            obj_data = json.loads(obj_data)
            data = obj_data[origin]

        except Exception:
            print("ERROR", traceback.format_exc())
            data = None
        return data

    def _get_s3_client(self):
        if self._role:
            sts_client = boto3.client('sts')
            assumed_role_object = sts_client.assume_role(
                RoleArn=self._role,
                RoleSessionName="AssumeRoleSession1"
            )
            credentials = assumed_role_object['Credentials']
            s3_client = boto3.client(
                service_name='s3',
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'])
        else:
            s3_client = boto3.client(
                service_name='s3'
            )
        return s3_client
