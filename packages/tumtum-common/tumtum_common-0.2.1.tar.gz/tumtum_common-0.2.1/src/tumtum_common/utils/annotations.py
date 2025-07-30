"""Common annotations for TumTum routers."""

from fastapi import Request, Depends, Query
from typing import Annotated
from caching.models import UserSession
from caching.common_formats import SESSION_KEY
from exceptions import UnauthorizedException
from caching.annotations import RedisClientAnnotation

#
# App state
#

def get_app_state(req: Request):
    return req.app.state

AppState = Annotated[
    dict,
    Depends(get_app_state)
]


#
# Common parameters
#

def get_common_params(
    page_number: int = Query(1, ge=0),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query(None),
    sort_order: str = Query(None)
):
    return {
        "page_number": page_number,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_order": sort_order
    }

CommonParams = Annotated[
    dict, 
    Depends(get_common_params)
]


#
# Current user
#

async def get_user_session(req: Request, redis_client: RedisClientAnnotation) -> UserSession:
    """Get a user by session from Redis.
    
    Args:
        session_id: The ID of the session.

    Returns:
        The user session from Redis.
    """
    session_id = req.cookies.get("session_id")

    raw_dict = await redis_client.get(
        SESSION_KEY.format(
            session_id=session_id
        )
    )

    return UserSession(**raw_dict)

CurrentUser = Annotated[
    UserSession,
    Depends(get_user_session)
]

