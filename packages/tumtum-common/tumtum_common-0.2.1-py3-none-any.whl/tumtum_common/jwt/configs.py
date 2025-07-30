"""Config classes for jwt."""

from dataclasses import dataclass

@dataclass
class JwtTokenConfig:
    exp_time: int
    secret_key: str
