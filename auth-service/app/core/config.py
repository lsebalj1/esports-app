from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    dynamodb_endpoint: str = "http://localhost:8000"
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    aws_access_key_id: str = "local"
    aws_secret_access_key: str = "local"
    aws_default_region: str = "eu-central-1"

settings = Settings()