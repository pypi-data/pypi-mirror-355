"""Annotations for jwt."""

from tumtum_common.exceptions import UnauthorizedException
from tumtum_common.jwt.core import validate_token
from tumtum_common.jwt.configs import JwtTokenConfig
from tumtum_common.jwt.models import JwtPayload

from fastapi import Request, Depends
from typing import Annotated

async def get_access_token(req: Request) -> str:
    """Get an access token from the request.

    Args:
        req: The request.
    
    Returns:
        The access token.
    """

    try:
        return req.cookies.get("access_token")
    except Exception as e:
        raise UnauthorizedException(f"Failed to get access token: {e}")
    
async def get_refresh_token(req: Request) -> str:
    """Get a refresh token from the request.
    
    Args:
        req: The request.
    
    Returns:
        The refresh token.
    """
    
    try:
        return req.cookies.get("refresh_token")
    except Exception as e:
        raise UnauthorizedException(f"Failed to get refresh token: {e}")
    
AccessToken = Annotated[
    str,
    Depends(get_access_token)
]

RefreshToken = Annotated[
    str,
    Depends(get_refresh_token)
]