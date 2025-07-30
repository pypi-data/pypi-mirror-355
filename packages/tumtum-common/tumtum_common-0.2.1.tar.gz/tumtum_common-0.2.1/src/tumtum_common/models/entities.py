"""This module defines the SQLAlchemy ORM models for the database entities used in the application."""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Date, UUID, Integer, ForeignKey, Table, Uuid
from sqlalchemy.orm import relationship
import datetime

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


#
# ASSOCIATION TABLES
#

video_like_association_table = Table(
    "video_likes_association_table",
    Base.metadata,
    Column("video_id", ForeignKey("videos.id"), primary_key=True),
    Column("users_id", ForeignKey("users_profiles.id"), primary_key=True)
)

video_tags_association_table = Table(
    "video_tags_association_table",
    Base.metadata,
    Column("video_id", ForeignKey("videos.id"), primary_key=True),
    Column("tag_id", ForeignKey("video_tags.id"), primary_key=True)
)


#
# USER'S MODELS
#

class UserCredits(Base):
    """Represents a user's credentials in the system.

    Attributes:    
        id (UUID): The unique identifier for the credentials.
        username (str): The username of the user.
        password (str): The hashed password of the user.
        email (str): The email address of the user.
        user (relationship): A one-to-one relationship with User, representing the user associated with these credentials.
    """

    __tablename__ = "users_credits"
    id = Column(UUID, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)

    user = relationship("User", back_populates="credits", lazy="select", uselist=False)

class UserProfile(Base):
    """Represents a user's profile in the system.

    Attributes:
        id (UUID): The unique identifier for the profile.
        name (str): The name of the user.
        profile_picture (str): The URL or path to the user's profile picture.
        subscribers_count (int): The number of subscribers the user has.
        subscriptions_count (int): The number of subscriptions the user has.
        created_at (Date): The date when the profile was created.
        status_id (int): The ID of the user's status, linked to UserStatus.
        status (relationship): A relationship to UserStatus, representing the user's status.
        subscribers (relationship): A one-to-many relationship with UserSubscriptionLine, representing users who subscribed to this profile.
        subscriptions (relationship): A one-to-many relationship with UserSubscriptionLine, representing profiles this user is subscribed to.
        videos (relationship): A one-to-many relationship with Video, representing videos uploaded by the user.
        liked_videos (relationship): A many-to-many relationship with Video, representing videos liked by the user.
        user (relationship): A one-to-one relationship with User, representing the user associated with this profile.
    """

    __tablename__ = "users_profiles"
    id = Column(UUID, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    profile_picture = Column(String, nullable=False)
    subscribers_count = Column(Integer, nullable=False, default=0)
    subscriptions_count = Column(Integer, nullable=False, default=0)
    created_at = Column(Date, nullable=False, default=datetime.datetime.now())

    status_id = Column(Integer, ForeignKey("users_statuses.id"), nullable=False, default=0)

    status = relationship(
        "UserStatus",
        back_populates="users",
        lazy="select",
        uselist=False
    )
    subscribers = relationship(
        "UserSubscriptionLine",
        back_populates="author",
        lazy="select"
    )
    subscriptions = relationship(
        "UserSubscriptionLine",
        back_populates="sub",
        lazy="select"
    )
    videos = relationship(
        "Video",
        back_populates="author",
        lazy="select"
    )
    liked_videos = relationship(
        "Video",
        secondary=video_like_association_table,
        back_populates="liked_users",
        lazy="select"                            
    )
    user = relationship(
        "User",
        back_populates="profile",
        lazy="select",
        uselist=False
    )

class User(Base):
    """Represents a user in the system.

    Attributes:
        id (UUID): The unique identifier for the user.
        credits_id (UUID): The ID of the user's credentials, linked to UserCredits.
        profile_id (UUID): The ID of the user's profile, linked to UserProfile.
        created_at (Date): The date when the user was created.
        role_id (int): The ID of the user's role, linked to UserRole.
        role (relationship): A relationship to UserRole, representing the user's role.
        credits (relationship): A relationship to UserCredits, representing the user's credentials.
        profile (relationship): A relationship to UserProfile, representing the user's profile.
    """

    __tablename__ = "users"
    id = Column(UUID, primary_key=True, nullable=False)
    credits_id = Column(UUID, ForeignKey("users_credits.id"), nullable=False)
    profile_id = Column(UUID, ForeignKey("users_profiles.id"), nullable=False)

    created_at = Column(Date, nullable=False, default=datetime.datetime.now())
    role_id = Column(Integer, ForeignKey("users_roles.id"), nullable=False, default=0)

    role = relationship("UserRole", back_populates="users", lazy="select", uselist=False)
    credits = relationship("UserCredits", back_populates="user", lazy="select", uselist=False)
    profile = relationship("UserProfile", back_populates="user", lazy="select", uselist=False)

class UserRole(Base):
    """Represents a role that a user can have.
    
    Attributes:
        id (int): The unique identifier for the role.
        role (str): The name of the role (e.g., 'admin', 'user').
        users (relationship): A one-to-many relationship with User.
    """

    __tablename__ = "users_roles"
    id = Column(Integer, nullable=False, primary_key=True)
    role = Column(String, nullable=False)

    users = relationship("User", back_populates="role", lazy="select")

class UserStatus(Base):
    """Represents the status of a user.
    
    Attributes:
        id (int): The unique identifier for the status.
        status (str): The status description (e.g., 'active', 'inactive').
        users (relationship): A one-to-many relationship with UserProfile.
    """

    __tablename__ = "users_statuses"
    id = Column(Integer, primary_key=True, nullable=False)
    status = Column(String, nullable=False)

    users = relationship("UserProfile", back_populates="status", lazy="select")

class UserSubscriptionLine(Base):
    """Represents a subscription line for a user.
    
    Attributes:
        id (int): The unique identifier for the subscription line.
        created_at (Date): The date when the subscription line was created.
        author_id (UUID): The ID of the user who is the author of the subscription.
        sub_id (UUID): The ID of the user who is subscribed.
        subscription_level_id (int): The ID of the subscription level.
        level (relationship): A relationship to UserSubscriptionLevel.
        author (relationship): A relationship to UserProfile, representing the author of the subscription.
        sub (relationship): A relationship to UserProfile, representing the subscriber.
    """

    __tablename__ = "users_subscriptions_lines"
    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(Date, nullable=False, default=datetime.datetime.now())

    author_id = Column(UUID, ForeignKey("users_profiles.id"), nullable=False)
    sub_id = Column(UUID, ForeignKey("users_profiles.id"), nullable=False)
    subscription_level_id = Column(Integer, ForeignKey("users_subscriptions_levels.id"), nullable=False)

    level = relationship("UserSubscriptionLevel", back_populates="subscription_lines", lazy="select", uselist=False)
    author = relationship("UserProfile", foreign_keys=[author_id], back_populates="subscribers", lazy="select", uselist=False)
    sub = relationship("UserProfile", foreign_keys=[sub_id], back_populates="subscriptions", lazy="select", uselist=False)

class UserSubscriptionLevel(Base):
    """Represents a subscription level for users.

    Attributes:
        id (int): The unique identifier for the subscription level.
        level (str): The name of the subscription level.
        subscription_lines (relationship): A one-to-many relationship with UserSubscriptionLine.
    """

    __tablename__ = "users_subscriptions_levels"
    id = Column(Integer, primary_key=True, nullable=False)
    level = Column(String, nullable=False)

    subscription_lines = relationship("UserSubscriptionLine", back_populates="level", lazy="select")


#
# VIDEO'S MODELS
#

class VideoTag(Base):
    """Represents a tag that can be associated with videos.
    
    Attributes:
        id (int): The unique identifier for the tag.
        tag_name (str): The name of the tag.
        videos (relationship): A many-to-many relationship with Video.
    """

    __tablename__ = "video_tags"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    tag_name = Column(String, nullable=False)

    videos = relationship(
        "Video",
        secondary=video_tags_association_table,
        back_populates="tags",
        lazy="select"
    )

class Video(Base):
    """Represents a video uploaded by a user.
    
    Attributes:
        id (UUID): The unique identifier for the video.
        title (str): The title of the video.
        description (str): A description of the video.
        file_video_path (str): The file path where the video is stored.
        created_at (Date): The date when the video was created.
        author_id (UUID): The ID of the user who uploaded the video.
        status_id (int): The status of the video, linked to VideoStatus.
        status (relationship): A relationship to VideoStatus.
        author (relationship): A relationship to UserProfile, representing the video's author.
        liked_users (relationship): A many-to-many relationship with UserProfile for users who liked the video.
        tags (relationship): A many-to-many relationship with VideoTag for associated tags.
    """

    __tablename__ = "videos"
    id = Column(UUID, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    file_video_path = Column(String, nullable=False)
    created_at = Column(Date, nullable=False, default=datetime.datetime.now())
    author_id = Column(UUID, ForeignKey("users_profiles.id"), nullable=False)
    status_id = Column(Integer, ForeignKey("video_statuses.id"), nullable=False, default=1)

    status = relationship("VideoStatus", back_populates="videos", lazy="select", uselist=False)
    author = relationship("UserProfile", back_populates="videos", lazy="select", uselist=False)
    liked_users = relationship(
        "UserProfile",
        secondary=video_like_association_table,
        back_populates="liked_videos" ,
        lazy="select"   
    )
    tags = relationship(
        "VideoTag",
        secondary=video_tags_association_table,
        back_populates="videos",
        lazy="select"
    )

class VideoStatus(Base):
    """Represents the status of a video.
    
    Attributes:
        id (int): The unique identifier for the status.
        status (str): The status description (e.g., 'active', 'inactive').
        videos (relationship): A one-to-many relationship with Video.
    """

    __tablename__ = "video_statuses"
    id = Column(Integer, primary_key=True, nullable=False)
    status = Column(String, nullable=False)

    videos = relationship("Video", back_populates="status", lazy="select")


