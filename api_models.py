#########################
# BLOCK WITH API MODELS #
#########################


from datetime import date
from typing import List
from fastapi import HTTPException
import uuid
import re
from pydantic import BaseModel, EmailStr, validator, UUID4


LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")


class TunedModel(BaseModel):
    class Config:
        """tells pydantic to convert even non dict obj to json"""

        from_attributes = True


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr
    language: str

    @validator("name")
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value

    @validator("surname")
    def validate_surname(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Surname should contains only letters"
            )
        return value


class ShowUser(TunedModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    language: str


class ShowUserWithAchievementsCount(TunedModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    language: str
    achievements_count: int


class ShowUserWithAchievementPoints(TunedModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    language: str
    total_points: int


class AchievementCreate(BaseModel):
    name: str
    points: int
    ru_description: str
    en_description: str


class ShowAchievement(TunedModel):
    achievement_id: uuid.UUID
    name: str
    points: int
    ru_description: str
    en_description: str


class ReceivedAchievementCreate(BaseModel):
    email: EmailStr
    achievement_name: str
    date: date

    class Config:
        arbitrary_types_allowed = True


class ShowReceivedAchievement(TunedModel):
    ra_id: uuid.UUID
    date: date
    name: str
    surname: str
    points: int
    description: str

    class Config:
        arbitrary_types_allowed = True


class UsersWithPointDifference(TunedModel):
    user1: dict
    user2: dict
    point_difference: int


class AchievementDetail(BaseModel):
    name: str
    date: date


class ShowUserWithAchievementsConsecutiveDays(BaseModel):
    user_id: UUID4
    name: str
    surname: str
    email: str
    language: str
    achievements: List[AchievementDetail]

    class Config:
        orm_mode = True

