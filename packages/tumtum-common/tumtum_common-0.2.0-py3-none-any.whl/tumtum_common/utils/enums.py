"""Common enums for TumTum services."""

from enum import Enum
from typing import Tuple, Optional
from models.entities import UserRole, UserStatus, VideoStatus


class BaseEnum(Enum):
    """Base enum class with common functionality."""
    
    def __init__(self, id: int, name: str):
        """Initialize the enum.
        
        Args:
            id: The ID of the enum.
            name: The name of the enum.
        """
        self.id = id
        self.name = name

    @classmethod
    def from_id(cls, id: int) -> Optional['BaseEnum']:
        """Get enum from ID.
        
        Args:
            id: The ID of the enum.
        """
        for item in cls:
            if item.id == id:
                return item
        return None

    @classmethod
    def from_name(cls, name: str) -> Optional['BaseEnum']:
        """Get enum from name.
        
        Args:
            name: The name of the enum.
        """
        for item in cls:
            if item.name == name:
                return item
        return None

    @classmethod
    def from_values(cls, id: int, name: str) -> Optional['BaseEnum']:
        """Get enum from values.
        
        Args:
            id: The ID of the enum.
            name: The name of the enum.
        """
        for item in cls:
            if item.id == id and item.name == name:
                return item
        return None

    def get_id(self) -> int:
        """Get the ID of the enum."""
        return self.id

    def get_name(self) -> str:
        """Get the name of the enum."""
        return self.name

    def get_values(self) -> Tuple[int, str]:
        """Get the values of the enum."""
        return (self.id, self.name)


class UserRoleEnum(BaseEnum):
    """User role enum.
    
    Attributes:
        USER: User role.
        MODER: Moderator role.
        STAFF: Staff role.
        ADMIN: Admin role.
    """
    
    USER = (1, "USER")
    MODER = (2, "MODER")
    STAFF = (3, "STAFF")
    ADMIN = (4, "ADMIN")

    @classmethod
    def from_entity(cls, entity: UserRole) -> Optional['UserRoleEnum']:
        """Get user role enum from entity."""
        return cls.from_id(entity.id)


class UserStatusEnum(BaseEnum):
    """User status enum.
    
    Attributes:
        BASE: Base status.
        BANNED: Banned status.
        ACCEPTED: Accepted status.
    """

    BASE = (1, "BASE")
    BANNED = (2, "BANNED")
    ACCEPTED = (3, "ACCEPTED")

    @classmethod
    def from_entity(cls, entity: UserStatus) -> Optional['UserStatusEnum']:
        """Get user status enum from entity."""
        return cls.from_id(entity.id)


class VideoStatusEnum(BaseEnum):
    """Video status enum.
    
    Attributes:
        WAIT_FOR_VIDEO_FILE: Wait for video file.
        ON_PRIMARY_MODERATION: On primary moderation.
        ON_CHECKING_MODERATION: On checking moderation.
        BANNED: Banned.
        ONLY_FRO_SUBS: Only for subs.
        ONLY_FOR_VIP_SUBS: Only for VIP subs.
        ONLY_FOR_PAID_SUBS: Only for paid subs.
        ONLY_BY_LINK: Only by link.
        HIDDEN: Hidden.
        PUBLIC: Public.
        WITHOUT_STATUS: Without status.
    """

    WAIT_FOR_VIDEO_FILE = (1, "WAIT_FOR_VIDEO_FILE")
    ON_PRIMARY_MODERATION = (2, "ON_PRIMARY_MODERATION")
    ON_CHECKING_MODERATION = (3, "ON_CHECKING_MODERATION")
    BANNED = (4, "BANNED")
    ONLY_FRO_SUBS = (5, "ONLY_FRO_SUBS")
    ONLY_FOR_VIP_SUBS = (6, "ONLY_FOR_VIP_SUBS")
    ONLY_FOR_PAID_SUBS = (7, "ONLY_FOR_PAID_SUBS")
    ONLY_BY_LINK = (8, "ONLY_BY_LINK")
    HIDDEN = (9, "HIDDEN")
    PUBLIC = (10, "PUBLIC")
    WITHOUT_STATUS = (11, "WITHOUT_STATUS")

    @classmethod
    def from_entity(cls, entity: VideoStatus) -> Optional['VideoStatusEnum']:
        """Get video status enum from entity."""
        return cls.from_id(entity.id)

