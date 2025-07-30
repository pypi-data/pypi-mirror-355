from buco_db_controller.models.odds import Odds
from buco_db_controller.repositories.odds_repository import OddsRepository
from buco_db_controller.services.fixture_service import FixtureService


class OddsService:
    def __init__(self):
        self.odds_repository = OddsRepository()
        self.fixture_service = FixtureService()

    def upsert_many_odds(self, odds: list):
        self.odds_repository.upsert_many_odds(odds)

    def insert_odds(self, odds: dict):
        self.odds_repository.insert_odds(odds)

    def get_team_odds(self, team_id: int, league_id: int, season: int) -> list[Odds]:
        fixture_ids = self.fixture_service.get_fixture_ids(team_id, league_id, season)
        team_odds = self.odds_repository.get_many_odds(fixture_ids)
        team_odds = [Odds.from_dict(response) for response in team_odds]

        return team_odds

    def get_league_odds(self, league_id: int, season: int) -> list[Odds]:
        league_odds = self.odds_repository.get_league_odds(league_id, season)
        league_odds = [Odds.from_dict(response) for response in league_odds]

        return league_odds
