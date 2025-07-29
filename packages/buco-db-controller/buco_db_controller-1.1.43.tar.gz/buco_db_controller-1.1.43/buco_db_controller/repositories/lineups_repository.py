import logging
from typing import List

from buco_db_controller.mongo_db.mongo_db_repository import MongoDBBaseRepository

logger = logging.getLogger(__name__)


class LineupsRepository(MongoDBBaseRepository):
    DB_NAME = 'api_football'

    def __init__(self):
        super().__init__(self.DB_NAME)

    def upsert_many_lineups(self, lineups: list):
        self.bulk_upsert_documents('lineups', lineups)
        logger.info('Upserted fixture lineups data')

    def get_lineups(self, fixture_id: int) -> dict:
        query = {'parameters.fixture': fixture_id}

        lineups = self.find_document('lineups', query)
        logger.info(f'Fetching lineups for fixture {fixture_id}')
        return lineups

    def get_many_lineups(self, fixture_ids: List[int]) -> list:
        query = {'parameters.fixture': {'$in': fixture_ids}}

        lineups = self.find_documents('lineups', query)
        logger.info(f'Fetching lineups for fixtures {fixture_ids}')
        return lineups
