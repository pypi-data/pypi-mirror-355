import logging
from typing import Optional

from buco_db_controller.models.uefa_ranking import UEFARanking
from buco_db_controller.repositories.uefa_ranking_repository import UEFARankingRepository
from buco_db_controller.utils import mappers

logger = logging.getLogger(__name__)


class UEFARankingService:
    def __init__(self):
        self.uefa_ranking_repository = UEFARankingRepository()

    def insert_uefa_ranking(self, uefa_ranking: dict):
        self.uefa_ranking_repository.insert_uefa_ranking(uefa_ranking)

    def upsert_many_uefa_ranking(self, uefa_ranking: list):
        self.uefa_ranking_repository.upsert_many_uefa_ranking(uefa_ranking)

    def get_uefa_ranking(self, season: int) -> Optional[UEFARanking]:
        response = self.uefa_ranking_repository.get_uefa_ranking(season)

        if not response.get('data', []):
            return None

        uefa_ranking = UEFARanking.from_dict(response)
        return uefa_ranking

    def get_country_uefa_ranking(self, country: str, season: int) -> Optional[float]:
        response = self.uefa_ranking_repository.get_uefa_ranking(season)

        if not response or not response.get('data', []):
            return None

        uefa_ranking = UEFARanking.from_dict(response)
        country = mappers.find_fuzzy_item(country, uefa_ranking.coefficients.keys(), error=False)
        coefficient = next(
            (coefficient for key, coefficient in uefa_ranking.coefficients.items() if key == country), None
        )
        return coefficient
