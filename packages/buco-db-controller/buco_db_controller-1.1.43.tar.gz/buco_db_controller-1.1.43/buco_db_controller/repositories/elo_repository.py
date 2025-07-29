import logging
from typing import List

from buco_db_controller.mongo_db.mongo_db_repository import MongoDBBaseRepository

logger = logging.getLogger(__name__)


class EloRepository(MongoDBBaseRepository):

    def __init__(self, db_name):
        super().__init__(db_name)

    def upsert_many_elo(self, elo: list):
        self.bulk_upsert_documents('elo', elo)
        logger.debug('Upserted fixture elo data')

    def get_elo(self, fixture_id: int) -> dict:
        query = {'parameters.fixture': fixture_id}
        elo = self.find_document('elo', query)
        logger.debug(f'Fetching elo for fixture {fixture_id}')
        return elo

    def get_many_elo(self, fixture_ids: List[int]) -> list:
        query = {'parameters.fixture': {'$in': fixture_ids}}
        elo = self.find_documents('elo', query)
        logger.debug(f'Fetching fbref elo for fixtures {fixture_ids}')
        return elo
