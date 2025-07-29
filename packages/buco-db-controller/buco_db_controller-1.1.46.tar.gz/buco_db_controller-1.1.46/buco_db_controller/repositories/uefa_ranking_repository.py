import logging

from buco_db_controller.mongo_db.mongo_db_repository import MongoDBBaseRepository

logger = logging.getLogger(__name__)


class UEFARankingRepository(MongoDBBaseRepository):
    DB_NAME = 'uefa'

    def __init__(self):
        super().__init__(self.DB_NAME)

    def insert_uefa_ranking(self, uefa_ranking: dict):
        self.insert_document('uefa_ranking', uefa_ranking)
        logger.debug('Inserted UEFA ranking data')

    def upsert_many_uefa_ranking(self, uefa_ranking: list):
        self.bulk_upsert_documents('uefa_ranking', uefa_ranking)
        logger.debug('Upsert UEFA ranking data')

    def get_uefa_ranking(self, season: int) -> dict:
        query = {'parameters.season': season}
        uefa_ranking = self.find_document('uefa_ranking', query)
        logger.debug(f'Fetching UEFA ranking for season {season}')
        return uefa_ranking
