from typing import Optional

from buco_db_controller.models.league_info import LeagueInfo
from buco_db_controller.repositories.league_info_repository import LeagueInfoRepository
from buco_db_controller.services.fixture_service import FixtureService


class LeagueInfoService:
    def __init__(self):
        self.league_info_repository = LeagueInfoRepository()
        self.fixture_service = FixtureService()

    def upsert_league_info(self, league_info: dict):
        self.league_info_repository.upsert_league_info(league_info)

    def get_team_league(self, league_id: int) -> Optional[LeagueInfo]:
        response = self.league_info_repository.get_league_info(league_id)

        if not response.get('data', []):
            return None

        league_info = LeagueInfo.from_dict(response)
        return league_info
