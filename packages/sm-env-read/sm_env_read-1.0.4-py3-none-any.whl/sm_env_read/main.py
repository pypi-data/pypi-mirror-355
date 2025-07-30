import boto3
import json
import base64
from botocore.exceptions import ClientError

def get_env_secrets_from_sm(
        account_id: str,
        region: str,
        role_name: str,
        secret_name: str
) -> dict:
    """
    This function will help to read the secrets from the secret manager.
    The function will go on the linear approach in order to read the secrets
    from the AWS secret manager. First the function will check for direct access
    if possible or not? if that failed function will go for role based auth 
    :param account_id: AWS account id
    :param region: AWS region
    :param role_name: AWS role name
    :param secret_name: AWS secret name
    :return: secret value as a dict
    """
    def get_secret_value(client):
        """Helper function to get and parse secret value"""
        secret_value_response = client.get_secret_value(SecretId=secret_name)
        
        if "SecretString" in secret_value_response:
            return json.loads(secret_value_response["SecretString"])
        else:
            decoded_binary_secret = base64.b64decode(
                secret_value_response["SecretBinary"]
            ).decode('utf-8')
            return json.loads(decoded_binary_secret)
        
    try:
        direct_client = boto3.client(
            service_name="secretsmanager",
            region_name=region,
        )
        return get_secret_value(direct_client)
    except ClientError as e:
        try:
            sts_client = boto3.client(
                service_name="sts",
                region_name=region,
            )
            assumed_role_object = sts_client.assume_role(
                RoleArn=f"arn:aws:iam::{account_id}:role/{role_name}",
                RoleSessionName="AssumeRoleSession1",
            )
            credentials = assumed_role_object["Credentials"]
            assumed_role_client = boto3.client(
                service_name="secretsmanager",
                region_name=region,
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )
            return get_secret_value(assumed_role_client)
        
        except ClientError as e:
            raise e
    