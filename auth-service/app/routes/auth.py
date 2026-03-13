import uuid
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_table
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
    VerifyResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)

def _get_user_by_email(email: str):
    table = get_table("Users")
    resp = table.query(
        IndexName="email-index",
        KeyConditionExpression=Key("email").eq(email),
    )
    items = resp.get("Items", [])
    return items[0] if items else None

def _get_user_by_id(user_id: str):
    table = get_table("Users")
    resp = table.get_item(Key={"user_id": user_id})
    return resp.get("Item")

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest):
    if _get_user_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "user_id": user_id,
        "username": payload.username,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": payload.role.value,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    get_table("Users").put_item(Item=item)

    token = create_access_token(
        {"sub": user_id, "username": payload.username, "role": payload.role.value}
    )
    user_public = UserPublic(**{k: v for k, v in item.items() if k != "password_hash"})
    return TokenResponse(access_token=token, user=user_public)

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = _get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Account inactive")

    token = create_access_token(
        {"sub": user["user_id"], "username": user["username"], "role": user["role"]}
    )
    user_public = UserPublic(**{k: v for k, v in user.items() if k != "password_hash"})
    return TokenResponse(access_token=token, user=user_public)

@router.get("/me", response_model=UserPublic)
def me(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = _get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic(**{k: v for k, v in user.items() if k != "password_hash"})

@router.post("/verify", response_model=VerifyResponse)
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        return VerifyResponse(valid=False, message="Missing token")
    try:
        payload = decode_token(credentials.credentials)
        return VerifyResponse(
            valid=True,
            user_id=payload["sub"],
            username=payload["username"],
            role=payload["role"],
        )
    except Exception as e:
        return VerifyResponse(valid=False, message=str(e))