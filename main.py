from fastapi import FastAPI, APIRouter
import uvicorn
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

import settings  # Импортируем настройки
from dals import *
from api_models import *


# create instance of the app
app = FastAPI(title="server-achievements")

##############################################
# BLOCK FOR COMMON INTERACTION WITH DATABASE #
##############################################


# create async engine for interaction with database
engine = create_async_engine(settings.REAL_DATABASE_URL, future=True, echo=True)

# create session for the interaction with database
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


#########################
# BLOCK WITH API ROUTES #
#########################


user_router = APIRouter()
achievement_router = APIRouter()
received_achievement_router = APIRouter()


async def _create_new_user(body: UserCreate) -> ShowUser:
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.create_user(
                name=body.name,
                surname=body.surname,
                email=body.email,
                language=body.language,
            )
            return ShowUser(
                user_id=user.user_id,
                name=user.name,
                surname=user.surname,
                email=user.email,
                language=user.language,
            )


@user_router.post("/", response_model=ShowUser)
async def create_user(body: UserCreate) -> ShowUser:
    return await _create_new_user(body)


@user_router.get("/", response_model=ShowUser)
async def get_user(email: str):
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.get_user(email)
            return ShowUser(
                user_id=user.user_id,
                name=user.name,
                surname=user.surname,
                email=user.email,
                language=user.language,
            )


@user_router.get("/most-achievements", response_model=ShowUserWithAchievementsCount)
async def get_user_with_most_achievements():
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user, achievements_count = await user_dal.get_user_with_most_achievements()
            return ShowUserWithAchievementsCount(
                user_id=user.user_id,
                name=user.name,
                surname=user.surname,
                email=user.email,
                language=user.language,
                achievements_count=achievements_count,
            )


@user_router.get("/most-achievement-points", response_model=ShowUserWithAchievementPoints)
async def get_user_with_most_achievement_points():
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user, total_points = await user_dal.get_user_with_most_achievement_points()
            return ShowUserWithAchievementPoints(
                user_id=user.user_id,
                name=user.name,
                surname=user.surname,
                email=user.email,
                language=user.language,
                total_points=total_points,
            )


@user_router.get("/max-point-difference", response_model=UsersWithPointDifference)
async def get_users_with_max_point_difference():
    async with async_session() as session:
        async with session.begin():
            received_achievement_dal = ReceivedAchievementsDAL(session)
            return await received_achievement_dal.get_users_with_max_point_difference_details()


@user_router.get("/min-point-difference", response_model=UsersWithPointDifference)
async def get_users_with_min_point_difference():
    async with async_session() as session:
        async with session.begin():
            received_achievement_dal = ReceivedAchievementsDAL(session)
            return await received_achievement_dal.get_users_with_min_point_difference_details()


@user_router.get("/achievements-seven-consecutive-days", response_model=List[ShowUserWithAchievementsConsecutiveDays])
async def get_users_with_achievements_for_seven_consecutive_days():
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            users = await user_dal.get_users_with_achievements_for_seven_consecutive_days()
            return [
                ShowUserWithAchievementsConsecutiveDays(
                    user_id=user_data["user"].user_id,
                    name=user_data["user"].name,
                    surname=user_data["user"].surname,
                    email=user_data["user"].email,
                    language=user_data["user"].language,
                    achievements=[
                        AchievementDetail(name=achievement["name"], date=achievement["date"])
                        for achievement in user_data["achievements"]
                    ]
                )
                for user_data in users
            ]


# Achievement Routes
@achievement_router.get("/", response_model=list[ShowAchievement])
async def get_all_achievements():
    async with async_session() as session:
        async with session.begin():
            achievement_dal = AchievementDAL(session)
            achievements = await achievement_dal.get_all_achievements()
            return achievements


@achievement_router.post("/", response_model=ShowAchievement)
async def create_achievement(body: AchievementCreate):
    async with async_session() as session:
        async with session.begin():
            achievement_dal = AchievementDAL(session)
            achievement = await achievement_dal.create_achievement(
                name=body.name,
                points=body.points,
                ru_description=body.ru_description,
                en_description=body.en_description,
            )
            return achievement


# Received Achievements Routes
@received_achievement_router.post("/", response_model=ShowReceivedAchievement)
async def create_received_achievement(body: ReceivedAchievementCreate):
    async with async_session() as session:
        async with session.begin():
            received_achievement_dal = ReceivedAchievementsDAL(session)
            received_achievement = await received_achievement_dal.create_received_achievement(
                email=body.email,
                achievement_name=body.achievement_name,  # Предполагается, что здесь body.name - это имя достижения
                date=body.date,
            )

        async with async_session() as new_session:
            async with new_session.begin():
                user_dal = UserDAL(new_session)
                user = await user_dal.get_user(body.email)

                achievement_dal = AchievementDAL(new_session)
                achievement = await achievement_dal.get_achievement_by_name(body.achievement_name)

            return ShowReceivedAchievement(
                ra_id=received_achievement.ra_id,
                date=received_achievement.date,
                name=user.name,
                surname=user.surname,
                points=achievement.points,
                description=achievement.ru_description if user.language == "ru" else achievement.en_description,
            )


@received_achievement_router.get("/", response_model=list[ShowReceivedAchievement])
async def get_user_achievements(email: str):
    async with async_session() as session:
        async with session.begin():
            received_achievement_dal = ReceivedAchievementsDAL(session)
            user_dal = UserDAL(session)
            achievement_dal = AchievementDAL(session)

            # Получаем пользователя
            user = await user_dal.get_user(email)

            # Получаем список полученных достижений пользователя
            received_achievements = await received_achievement_dal.get_received_achievements_by_email(email)

            # Собираем данные для каждого достижения
            user_achievements = []
            for ra in received_achievements:
                achievement = await achievement_dal.get_achievement_by_id(ra.achievement_id)
                user_achievements.append(
                    ShowReceivedAchievement(
                        ra_id=ra.ra_id,
                        date=ra.date,
                        name=user.name,
                        surname=user.surname,
                        points=achievement.points,
                        description=achievement.ru_description if user.language == "ru" else achievement.en_description,
                    )
                )
            return user_achievements


# create the instance for the routes
main_api_router = APIRouter()

# set routes to the app instance
main_api_router.include_router(user_router, prefix="/user", tags=["user"])
main_api_router.include_router(achievement_router, prefix="/achievement", tags=["achievement"])
main_api_router.include_router(received_achievement_router, prefix="/received-achievement",
                               tags=["received-achievement"])
app.include_router(main_api_router)

if __name__ == "__main__":
    # run app on the host and port
    uvicorn.run(app, host="localhost", port=8000)
