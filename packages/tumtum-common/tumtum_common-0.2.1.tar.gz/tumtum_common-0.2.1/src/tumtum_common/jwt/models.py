"""Payloads models"""

from pydantic import BaseModel

class JwtPayload(BaseModel):
    id: str
    sub: str
    role: str
    exp: int
