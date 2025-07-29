from typing import Optional

from buco_db_controller.models.elo import Elo
from buco_db_controller.repositories.elo_repository import EloRepository
from buco_db_controller.services.fixture_service import FixtureService


class EloService:
    def __init__(self):
        self.elo_repository = EloRepository('elo_football')
        self.fixture_service = FixtureService()

    def upsert_many_elo(self, elo: list[dict]):
        self.elo_repository.upsert_many_elo(elo)

    def get_elo(self, fixture_id: int) -> Optional[Elo]:
        elo = self.elo_repository.get_elo(fixture_id)

        if not elo:
            return None

        elo = Elo.from_dict(elo)
        return elo

    def get_elo_over_season(self, team_id: int, league_id: int, season: int) -> list[Elo]:
        fixture_ids = self.fixture_service.get_fixture_ids(team_id, league_id, season)
        elo = [Elo.from_dict(x) for x in self.elo_repository.get_many_elo(fixture_ids)]
        return elo

    def get_h2h_elo(self, team1_id: int, team2_id: int, league_id: int, season: int) -> list[Elo]:
        h2h_fixture_ids = self.fixture_service.get_h2h_fixture_ids(team1_id, team2_id, league_id, season)
        h2h_elo = [Elo.from_dict(x) for x in self.elo_repository.get_many_elo(h2h_fixture_ids)]
        return h2h_elo

    def has_elo(self, league_id: int, season: int) -> bool:
        fixture_ids = self.fixture_service.get_league_fixture_ids(league_id, season)
        elo = self.elo_repository.get_many_elo(fixture_ids)
        return bool(elo)
