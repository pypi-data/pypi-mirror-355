"""Core functions for jwt."""

from tumtum_common.logging.wrappers import log_entrance_debug
from tumtum_common.exceptions import UnauthorizedException
from tumtum_common.jwt.configs import JwtTokenConfig
from tumtum_common.jwt.models import JwtPayload

import datetime
import logging
import jwt

logger: logging.Logger = logging.getLogger(__name__)


@log_entrance_debug(logger)
async def create_token(username: str, user_id: str, role: str, config: JwtTokenConfig) -> str:
    payload = JwtPayload(
        id=user_id,
        sub=username,
        role=role,
        exp=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=config.exp_time)
    )
    
    token = jwt.encode(payload=payload.model_dump(), key=config.secret_key, algorithm="HS256")
    return token

@log_entrance_debug(logger)
async def validate_token(token: str, config: JwtTokenConfig) -> JwtPayload:
    try:
        payload = jwt.decode(jwt=token, key=config.secret_key, algorithms=["HS256"])
        return JwtPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Token expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid token")
