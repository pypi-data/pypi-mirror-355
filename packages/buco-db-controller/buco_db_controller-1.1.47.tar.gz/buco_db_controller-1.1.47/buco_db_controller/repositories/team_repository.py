import logging
from typing import List, Union

from buco_db_controller.mongo_db.mongo_db_repository import MongoDBBaseRepository

logger = logging.getLogger(__name__)


class TeamRepository(MongoDBBaseRepository):
    DB_NAME = 'api_football'

    def __init__(self):
        super().__init__(self.DB_NAME)

    def upsert_many_teams(self, teams: list):
        self.bulk_upsert_documents('teams', teams)
        logger.debug('Upserted teams data')

    def get_teams(self, league_id: int, season: int) -> dict:
        query = {'parameters.league': league_id, 'parameters.season': season}

        teams = self.find_document('teams', query)
        logger.debug(f'Fetching teams for league {league_id} for season {season}')
        return teams

    def get_many_teams(self, league_id: int, seasons: Union[int, List[int]]) -> list:
        seasons = [seasons] if isinstance(seasons, int) else seasons
        query = {'parameters.season': {'$in': seasons}, 'parameters.league': league_id}

        teams = self.find_documents('teams', query)
        logger.debug(f'MongoDB: Fetching teams for league {league_id} for seasons {seasons}')
        return teams

    def upsert_many_team_stats(self, team_stats: list):
        self.bulk_upsert_documents('teams_stats', team_stats)
        logger.debug('Upserted team stats data')

    def get_team_stats(self, team_id: int, league_id: int, season: int) -> dict:
        query = {'parameters.team': team_id, 'parameters.league': league_id, 'parameters.season': season}

        team_stats = self.find_document('teams_stats', query)
        logger.debug(f'Fetching stats for team {team_id} for league {league_id} for season {season}')
        return team_stats
