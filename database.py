##############################
# BLOCK WITH DATABASE MODELS #
##############################


from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    language = Column(String, nullable=False)


class Achievement(Base):
    __tablename__ = "achievements"

    achievement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    points = Column(Integer, nullable=False)
    ru_description = Column(String, nullable=False)
    en_description = Column(String, nullable=False)


class ReceivedAchievements(Base):
    __tablename__ = "received_achievements"

    ra_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.achievement_id'))
    date = Column(Date, nullable=False)
