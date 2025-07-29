from typing import Optional

from buco_db_controller import League
from buco_db_controller.repositories.team_league_repository import TeamLeaguesRepository
from buco_db_controller.services.fixture_service import FixtureService


class TeamLeagueService:
    def __init__(self):
        self.team_league_repository = TeamLeaguesRepository()
        self.fixture_service = FixtureService()

    def upsert_many_team_leagues(self, fixture_lineups: list):
        self.team_league_repository.bulk_upsert_documents('team_leagues', fixture_lineups)

    def get_team_league(self, team_id: int, season: int) -> Optional[League]:
        response = self.team_league_repository.get_team_league(team_id, season)

        if not response.get('data', []):
            return None

        league = League.from_dict(response)
        return league
