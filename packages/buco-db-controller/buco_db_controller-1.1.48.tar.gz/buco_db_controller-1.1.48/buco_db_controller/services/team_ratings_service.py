from typing import Optional

from buco_db_controller.models.team_ratings import TeamRatings
from buco_db_controller.repositories.team_ratings_repository import TeamRatingsRepository
from buco_db_controller.utils import mappers


class TeamRatingsService:
    def __init__(self):
        self.team_ratings_repository = TeamRatingsRepository()

    def upsert_many_team_ratings(self, team_ratings: list):
        self.team_ratings_repository.upsert_many_team_ratings(team_ratings)

    def insert_team_ratings(self, team_ratings: dict):
        self.team_ratings_repository.insert_team_ratings(team_ratings)

    def get_team_ratings(self, season: int) -> Optional[TeamRatings]:
        response = self.team_ratings_repository.get_team_ratings(season)
        if not response or not response.get('data', []):
            return None

        return TeamRatings.from_dict(response)
