import logging

from buco_db_controller.mongo_db.mongo_db_repository import MongoDBBaseRepository

logger = logging.getLogger(__name__)


class LeagueInfoRepository(MongoDBBaseRepository):
    DB_NAME = 'api_football'

    def __init__(self):
        super().__init__(self.DB_NAME)

    def upsert_league_info(self, league_info: dict):
        self.upsert_document('league_info', league_info)
        logger.debug('Upserted league_info data')

    def get_league_info(self, league_id: int) -> dict:
        query = {'parameters.id': league_id}

        league = self.find_document('league_info', query)
        logger.debug(f'Fetching league info for league {league_id}')
        return league
