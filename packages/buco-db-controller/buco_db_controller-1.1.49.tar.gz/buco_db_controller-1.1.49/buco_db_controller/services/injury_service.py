import logging

from buco_db_controller.models.injury import Injury
from buco_db_controller.repositories.injury_repository import InjuryRepository
from buco_db_controller.services.fixture_service import FixtureService


class InjuriesService:
    def __init__(self):
        self.injuries_repository = InjuryRepository()
        self.fixture_service = FixtureService()

    def upsert_many_injuries(self, fixture_injuries: list):
        self.injuries_repository.bulk_upsert_documents('injuries', fixture_injuries)

    def upsert_injuries(self, fixture_injuries: dict):
        self.injuries_repository.upsert_document('injuries', fixture_injuries)

    def get_injuries(self, fixture_id: int) -> list[Injury]:
        response = self.injuries_repository.get_injuries(fixture_id)

        if not response.get('data', []):
            return []

        fixture_stats = [Injury.from_dict(injury) for injury in response]
        return fixture_stats

    def get_team_injuries_per_fixture(self, team_id: int, league_id: int, season: int) -> list[dict[int, list[Injury]]]:
        fixture_ids = self.fixture_service.get_fixture_ids(team_id, league_id, season)
        team_injuries = self.injuries_repository.get_many_injuries(fixture_ids)
        team_injuries = [{fixture['fixture_id']: [Injury.from_dict(injury) for injury in fixture]} for fixture in team_injuries]
        return team_injuries
