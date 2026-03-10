import boto3
from app.core.config import settings

_dynamodb = None


def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=settings.dynamodb_endpoint,
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    return _dynamodb


def get_table(name: str):
    return get_dynamodb().Table(name)
