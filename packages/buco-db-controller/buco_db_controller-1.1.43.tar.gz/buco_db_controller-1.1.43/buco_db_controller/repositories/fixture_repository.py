import logging
from typing import List, Union

from buco_db_controller.mongo_db.mongo_db_repository import MongoDBBaseRepository

logger = logging.getLogger(__name__)


class FixtureRepository(MongoDBBaseRepository):
    DB_NAME = 'api_football'

    def __init__(self):
        super().__init__(self.DB_NAME)

    def upsert_many_fixtures(self, fixtures: list):
        self.bulk_upsert_documents('fixtures', fixtures)
        logger.debug('Upsert fixtures data')

    def upsert_many_fixtures_before(self, fixtures: list):
        self.bulk_upsert_documents('fixtures_before', fixtures)
        logger.debug('Upsert fixtures-before data')

    def get_team_fixtures(self, team_id: int, league_id: int, seasons: Union[int, List[int]]) -> list:
        seasons = [seasons] if isinstance(seasons, int) else seasons
        query = {'parameters.team': team_id, 'parameters.league': league_id, 'parameters.season': {'$in': seasons}}

        fixtures = self.find_documents('fixtures', query)
        logger.debug(f'Fetching fixtures for team {team_id} for league {league_id} for season {seasons}')
        return fixtures

    def get_league_fixtures(self, league_id: int, seasons: Union[int, List[int]]) -> list:
        seasons = [seasons] if isinstance(seasons, int) else seasons
        query = {'parameters.league': league_id, 'parameters.season': {'$in': seasons}}

        fixtures = self.find_documents('fixtures', query)
        logger.debug(f'Fetching fixtures for league {league_id} for season {seasons}')
        return fixtures

    def upsert_many_rounds(self, league_rounds: list):
        self.bulk_upsert_documents('league_rounds', league_rounds)
        logger.debug('Upsert league rounds data')

    def get_rounds(self, league_id: int, season: int) -> dict:
        query = {'parameters.league': league_id, 'parameters.season': season}

        league_rounds = self.find_document('league_rounds', query)
        logger.debug(f'Fetching league rounds for league {league_id} | season {season}')
        return league_rounds

    def get_fixture(self, fixture_id: int) -> dict:
        query = {'parameters.fixture': fixture_id}

        fixture = self.find_document('fixtures', query)
        logger.debug(f'Fetching fixture {fixture_id}')
        return fixture

    # deprecated
    def get_h2h_fixtures(self, team1_id: int, team2_id: int, league_id: int, seasons: Union[int, List[int]]) -> list:
        teams = [team1_id, team2_id]
        seasons = [seasons] if isinstance(seasons, int) else seasons

        query = {'parameters.team': {'$in': teams}, 'parameters.league': league_id, 'parameters.season': {'$in': seasons}}
        fixtures = self.find_documents('fixtures', query)
        logger.debug(f'Fetching H2H fixture for team {team1_id} vs team {team2_id} for league {league_id} for season {seasons}')
        return fixtures
