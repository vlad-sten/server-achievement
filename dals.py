###########################################################
# BLOCK FOR INTERACTION WITH DATABASE IN BUSINESS CONTEXT #
###########################################################


from datetime import date
from fastapi import HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import *


class UserDAL:
    """Data Access Layer for operating user info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(
            self, name: str, surname: str, email: str, language: str,
    ) -> User:
        new_user = User(
            name=name,
            surname=surname,
            email=email,
            language=language,
        )
        self.db_session.add(new_user)
        await self.db_session.flush()
        return new_user

    async def get_user(self, email: str) -> User:
        result = await self.db_session.execute(
            select(User).filter_by(email=email)
        )
        user = result.scalar()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        result = await self.db_session.execute(
            select(User).filter_by(user_id=user_id)
        )
        user = result.scalar()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_user_with_most_achievements(self) -> (User, int):
        result = await self.db_session.execute(
            select(User, func.count(ReceivedAchievements.ra_id).label('achievements_count'))
            .join(ReceivedAchievements, User.user_id == ReceivedAchievements.user_id)
            .group_by(User.user_id)
            .order_by(desc('achievements_count'))
            .limit(1)
        )
        user, achievements_count = result.first()
        if user is None:
            raise HTTPException(status_code=404, detail="No users found")
        return user, achievements_count

    async def get_user_with_most_achievement_points(self) -> (User, int):
        result = await self.db_session.execute(
            select(User, func.sum(Achievement.points).label('total_points'))
            .join(ReceivedAchievements, User.user_id == ReceivedAchievements.user_id)
            .join(Achievement, ReceivedAchievements.achievement_id == Achievement.achievement_id)
            .group_by(User.user_id)
            .order_by(desc('total_points'))
            .limit(1)
        )
        user, total_points = result.first()
        if user is None:
            raise HTTPException(status_code=404, detail="No users found")
        return user, total_points

    async def get_users_with_max_point_difference(self):
        stmt = (
            select(
                User.user_id,
                User.name,
                User.surname,
                func.sum(Achievement.points).label("total_points")
            )
            .join(ReceivedAchievements, User.user_id == ReceivedAchievements.user_id)
            .join(Achievement, ReceivedAchievements.achievement_id == Achievement.achievement_id)
            .group_by(User.user_id, User.name, User.surname)
            .order_by(func.sum(Achievement.points).desc())
        )

        result = await self.db_session.execute(stmt)
        users = result.fetchall()

        if len(users) < 2:
            raise HTTPException(status_code=404, detail="Not enough users to compare")

        # max_points = users[0][3]  # Исправляем индексацию на целочисленные значения
        # second_max_points = users[len(users)][3]

        diffs = []
        for j in range(len(users)):
            for i in range(len(users)):
                if i < j:
                    d = users[i][3] - users[j][3]
                    diff = (i, j, d)
                    diffs.append(diff)
                else:
                    break
        print(diffs)
        difference = max(diffs, key=lambda x: x[2])
        user1_number = difference[0]
        user2_number = difference[1]
        max_difference = difference[2]

        return {
            "user1": {
                "user_id": str(users[user1_number][0]),  # Преобразуем user_id к строке, если нужно
                "name": users[user1_number][1],
                "surname": users[user1_number][2],
                "total_points": users[user1_number][3],
            },
            "user2": {
                "user_id": str(users[user2_number][0]),  # Преобразуем user_id к строке, если нужно
                "name": users[user2_number][1],
                "surname": users[user2_number][2],
                "total_points": users[user2_number][3],
            },
            "point_difference": max_difference,
        }

    async def get_users_with_min_point_difference(self):
        stmt = (
            select(
                User.user_id,
                User.name,
                User.surname,
                func.sum(Achievement.points).label("total_points")
            )
            .join(ReceivedAchievements, User.user_id == ReceivedAchievements.user_id)
            .join(Achievement, ReceivedAchievements.achievement_id == Achievement.achievement_id)
            .group_by(User.user_id, User.name, User.surname)
            .order_by(func.sum(Achievement.points).desc())
        )

        result = await self.db_session.execute(stmt)
        users = result.fetchall()

        if len(users) < 2:
            raise HTTPException(status_code=404, detail="Not enough users to compare")

        diffs = []
        for j in range(len(users)):
            for i in range(len(users)):
                if i < j:
                    d = users[i][3] - users[j][3]
                    diff = (i, j, d)
                    diffs.append(diff)
                else:
                    break
        print(diffs)
        difference = min(diffs, key=lambda x: x[2])
        user1_number = difference[0]
        user2_number = difference[1]
        max_difference = difference[2]

        return {
            "user1": {
                "user_id": str(users[user1_number][0]),  # Преобразуем user_id к строке, если нужно
                "name": users[user1_number][1],
                "surname": users[user1_number][2],
                "total_points": users[user1_number][3],
            },
            "user2": {
                "user_id": str(users[user2_number][0]),  # Преобразуем user_id к строке, если нужно
                "name": users[user2_number][1],
                "surname": users[user2_number][2],
                "total_points": users[user2_number][3],
            },
            "point_difference": max_difference,
        }

    async def get_users_with_achievements_for_seven_consecutive_days(self):
        result = await self.db_session.execute(
            select(
                User.user_id,
                User.name,
                User.surname,
                User.email,
                User.language,
                func.array_agg(ReceivedAchievements.date).label('dates'),
                func.array_agg(Achievement.name).label('achievement_names')
            )
            .join(ReceivedAchievements, User.user_id == ReceivedAchievements.user_id)
            .join(Achievement, ReceivedAchievements.achievement_id == Achievement.achievement_id)
            .group_by(User.user_id)
        )
        users_with_achievements = result.fetchall()

        eligible_users = []
        for user in users_with_achievements:
            if self._check_seven_consecutive_days(user.dates):
                achievements = [
                    {"name": achievement_name, "date": date}
                    for achievement_name, date in zip(user.achievement_names, user.dates)
                ]
                eligible_users.append({
                    "user": user,
                    "achievements": achievements
                })

        return eligible_users

    def _check_seven_consecutive_days(self, dates):
        if len(dates) < 7:
            return False

        dates = sorted(dates)
        consecutive_days_count = 1
        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                consecutive_days_count += 1
                if consecutive_days_count == 7:
                    return True
            else:
                consecutive_days_count = 1
        return False


# Achievement DAL (добавляем метод для получения всех достижений и добавления достижения)
class AchievementDAL:
    """Data Access Layer for operating achievements"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_all_achievements(self):
        result = await self.db_session.execute(select(Achievement))
        return result.scalars().all()

    async def create_achievement(self, name: str, points: int, ru_description: str, en_description: str) -> Achievement:
        new_achievement = Achievement(
            name=name,
            points=points,
            ru_description=ru_description,
            en_description=en_description,
        )
        self.db_session.add(new_achievement)
        await self.db_session.flush()
        return new_achievement

    async def get_achievement_by_id(self, achievement_id: uuid.UUID) -> Achievement:
        result = await self.db_session.execute(
            select(Achievement).filter_by(achievement_id=achievement_id)
        )
        achievement = result.scalar()
        if achievement is None:
            raise HTTPException(status_code=404, detail="Achievement not found")
        return achievement

    async def get_achievement_by_name(self, name: str) -> Achievement:
        result = await self.db_session.execute(
            select(Achievement).filter_by(name=name)
        )
        achievement = result.scalar()
        if achievement is None:
            raise HTTPException(status_code=404, detail="Achievement not found")
        return achievement

    async def get_total_points_by_user_id(self, user_id: uuid.UUID):
        stmt = (
            select(func.sum(Achievement.points))
            .join(ReceivedAchievements, Achievement.achievement_id == ReceivedAchievements.achievement_id)
            .filter(ReceivedAchievements.user_id == user_id)
            .group_by(ReceivedAchievements.user_id)
        )
        result = await self.db_session.execute(stmt)
        total_points = result.scalar_one_or_none()
        return total_points if total_points else 0


class ReceivedAchievementsDAL:
    """Data Access Layer for operating received achievements"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_received_achievement(
            self, email: str, achievement_name: str, date: date
    ) -> ReceivedAchievements:
        # Получаем пользователя по email
        user_result = await self.db_session.execute(
            select(User).filter_by(email=email)
        )
        user = user_result.scalar()
        if user is None:
            raise HTTPException(status_code=404, detail=f"User with email '{email}' not found")

        # Получаем достижение по имени
        achievement_result = await self.db_session.execute(
            select(Achievement).filter_by(name=achievement_name)
        )
        achievement = achievement_result.scalar()
        if achievement is None:
            raise HTTPException(status_code=404, detail=f"Achievement with name '{achievement_name}' not found")

        # Создаем запись о полученном достижении
        new_received_achievement = ReceivedAchievements(
            user_id=user.user_id,
            achievement_id=achievement.achievement_id,
            date=date
        )
        self.db_session.add(new_received_achievement)
        await self.db_session.commit()  # Сохраняем изменения в базе
        return new_received_achievement

    async def get_user(self, email: str) -> User:
        result = await self.db_session.execute(
            select(User).filter_by(email=email)
        )
        user = result.scalar()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_achievement_by_name(self, name: str) -> Achievement:
        result = await self.db_session.execute(
            select(Achievement).filter_by(name=name)
        )
        achievement = result.scalar()
        if achievement is None:
            raise HTTPException(status_code=404, detail="Achievement not found")
        return achievement

    async def get_received_achievements_by_email(self, email: str):
        user_result = await self.db_session.execute(
            select(User).filter_by(email=email)
        )
        user = user_result.scalar()
        if user is None:
            raise HTTPException(status_code=404, detail=f"User with email '{email}' not found")

        result = await self.db_session.execute(
            select(ReceivedAchievements).filter_by(user_id=user.user_id)
        )
        return result.scalars().all()

    async def get_users_with_max_point_difference_details(self):
        user_dal = UserDAL(self.db_session)
        achievement_dal = AchievementDAL(self.db_session)

        max_points_data = await user_dal.get_users_with_max_point_difference()
        user1_id = max_points_data["user1"]["user_id"]
        user2_id = max_points_data["user2"]["user_id"]

        user1_points = await achievement_dal.get_total_points_by_user_id(user1_id)
        user2_points = await achievement_dal.get_total_points_by_user_id(user2_id)

        max_points_data["user1"]["total_points"] = user1_points
        max_points_data["user2"]["total_points"] = user2_points

        return max_points_data

    async def get_users_with_min_point_difference_details(self):
        user_dal = UserDAL(self.db_session)
        achievement_dal = AchievementDAL(self.db_session)

        min_points_data = await user_dal.get_users_with_min_point_difference()
        user1_id = min_points_data["user1"]["user_id"]
        user2_id = min_points_data["user2"]["user_id"]

        user1_points = await achievement_dal.get_total_points_by_user_id(user1_id)
        user2_points = await achievement_dal.get_total_points_by_user_id(user2_id)

        min_points_data["user1"]["total_points"] = user1_points
        min_points_data["user2"]["total_points"] = user2_points

        return min_points_data

