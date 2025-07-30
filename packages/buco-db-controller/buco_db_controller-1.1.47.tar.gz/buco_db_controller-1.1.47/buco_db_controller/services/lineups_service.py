from typing import Optional

from buco_db_controller.models.lineups import Lineups
from buco_db_controller.repositories.lineups_repository import LineupsRepository
from buco_db_controller.services.fixture_service import FixtureService


class LineupsService:
    def __init__(self):
        self.lineups_repository = LineupsRepository()
        self.fixture_service = FixtureService()

    def upsert_many_lineups(self, fixture_lineups: list):
        self.lineups_repository.bulk_upsert_documents('lineups', fixture_lineups)

    def get_lineups(self, fixture_id: int) -> Optional[Lineups]:
        response = self.lineups_repository.get_lineups(fixture_id)

        if not response.get('data', []):
            return None

        lineups = Lineups.from_dict(response)
        return lineups

    def get_team_lineups(self, team_id: int, league_id: int, season: int) -> list[Lineups]:
        fixture_ids = self.fixture_service.get_fixture_ids(team_id, league_id, season)
        lineups = self.lineups_repository.get_many_lineups(fixture_ids)
        lineups = [Lineups.from_dict(lineup) for lineup in lineups]

        return lineups

    def get_league_lineups(self, league_id: int, season: int) -> list[Lineups]:
        fixture_ids = self.fixture_service.get_league_fixture_ids(league_id, season)
        lineups = self.lineups_repository.get_many_lineups(fixture_ids)
        lineups = [Lineups.from_dict(lineup) for lineup in lineups]

        return lineups
