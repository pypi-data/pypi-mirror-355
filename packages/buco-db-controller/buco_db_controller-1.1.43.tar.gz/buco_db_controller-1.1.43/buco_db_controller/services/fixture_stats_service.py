from typing import List

from buco_db_controller.models.fixture_stats import FixtureStats
from buco_db_controller.repositories.fixture_stats_repository import FixtureStatsRepository
from buco_db_controller.services.fixture_service import FixtureService


class FixtureStatsService:
    apifootball = 'apifootball'
    flashscore = 'flashscore'

    def __init__(self):
        self.api_football_repository = FixtureStatsRepository('api_football')
        self.flashscore_repository = FixtureStatsRepository(self.flashscore)
        self.fixture_service = FixtureService()

    def upsert_many_fixture_stats(self, fixture_stats: list, source: str):
        if source == self.apifootball:
            self.api_football_repository.upsert_many_fixture_stats(fixture_stats)
        elif source == self.flashscore:
            self.flashscore_repository.upsert_many_fixture_stats(fixture_stats)

    def get_fixture_stats(self, fixture_id: int) -> dict[str, FixtureStats]:
        api_football_response = self.api_football_repository.get_fixture_stats(fixture_id)
        flashscore_response = self.flashscore_repository.get_fixture_stats(fixture_id)

        if not api_football_response.get('data', []) and not flashscore_response.get('data', []):
            # TODO: Investigate if this can be replaced with return None
            raise ValueError(f'No fixture stats found for fixture {fixture_id}')

        api_football_fixture_stats = FixtureStats.from_dict(api_football_response)
        flashscore_fixture_stats = FixtureStats.from_dict(flashscore_response)

        fixture_stats = {
            self.apifootball: api_football_fixture_stats,
            self.flashscore: flashscore_fixture_stats,
        }
        return fixture_stats

    def get_fixture_stats_over_season(self, team_id: int, league_id: int, season: int) -> dict[str, List[FixtureStats]]:
        fixture_ids = self.fixture_service.get_fixture_ids(team_id, league_id, season)
        api_football_fixture_stats = self._get_fixture_stats_by_fixture_ids(fixture_ids, self.api_football_repository)
        flashscore_fixture_stats = self._get_fixture_stats_by_fixture_ids(fixture_ids, self.flashscore_repository)
        fixture_stats = {
            self.apifootball: api_football_fixture_stats,
            self.flashscore: flashscore_fixture_stats,
        }
        return fixture_stats

    @classmethod
    def _get_fixture_stats_by_fixture_id(cls, fixture_id: int, repository: FixtureStatsRepository) -> list[FixtureStats]:
        fixture_stats = repository.get_fixture_stats(fixture_id)
        fixture_stats = [FixtureStats.from_dict(fixture_stat) for fixture_stat in fixture_stats]
        return fixture_stats

    @classmethod
    def _get_fixture_stats_by_fixture_ids(cls, fixture_ids: List[int], repository: FixtureStatsRepository) -> list[FixtureStats]:
        fixture_stats = repository.get_many_fixture_stats(fixture_ids)
        fixture_stats = [FixtureStats.from_dict(fixture_stat) for fixture_stat in fixture_stats]
        return fixture_stats
