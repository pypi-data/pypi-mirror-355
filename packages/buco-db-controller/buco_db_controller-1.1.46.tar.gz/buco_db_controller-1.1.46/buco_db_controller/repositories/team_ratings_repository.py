import logging

from buco_db_controller.mongo_db.mongo_db_repository import MongoDBBaseRepository

logger = logging.getLogger(__name__)


class TeamRatingsRepository(MongoDBBaseRepository):
    DB_NAME = 'sofifa'

    def __init__(self):
        super().__init__(self.DB_NAME)

    def upsert_many_team_ratings(self, team_ratings: list):
        self.bulk_upsert_documents('team_ratings', team_ratings)
        logger.debug('Upsert team ratings data')

    def insert_team_ratings(self, team_ratings: dict):
        self.insert_document('team_ratings', team_ratings)
        logger.debug('Inserted team ratings data')

    def get_team_ratings(self, season: int) -> dict:
        query = {'parameters.season': season}

        team_ratings = self.find_document('team_ratings', query)
        logger.debug(f'Fetching odds for season {season}')
        return team_ratings
