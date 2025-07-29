from typing import List, Dict, Union

from buco_db_controller import FixtureService
from buco_db_controller.models.teams_stats import TeamStats
from buco_db_controller.repositories.team_stats_repository import TeamStatsRepository


class TeamStatsService:
    def __init__(self):
        self.team_repository = TeamStatsRepository()
        self.fixture_service = FixtureService()

    def upsert_many_team_stats(self, team_stats: List[dict]):
        self.team_repository.upsert_many_team_stats(team_stats)

    def get_league_team_stats(self, team_id: int, league: int, seasons: Union[int, List[int]]) -> List[TeamStats]:
        response = self.team_repository.get_league_team_stats(team_id, league, seasons)
        teams_stats = [TeamStats.from_dict(team_stats) for team_stats in response]
        return teams_stats

    def get_fixture_team_stats(self, fixture_id: int) -> List[TeamStats]:
        response = self.team_repository.get_fixture_team_stats(fixture_id)
        teams_stats = [TeamStats.from_dict(team_stats) for team_stats in response]
        return teams_stats

    def get_h2h_team_stats(self, team1_id: int, team2_id: int, league_id: int, seasons: Union[int, List[int]]) -> Dict[str, List[TeamStats]]:
        team1_stats = self.get_league_team_stats(team1_id, league_id, seasons)
        team2_stats = self.get_league_team_stats(team2_id, league_id, seasons)

        team2_stats_fixture_ids = [fixture.fixture_id for fixture in team2_stats]
        team1_stats_fixture_ids = [fixture.fixture_id for fixture in team1_stats]

        team1_stats = [fixture for fixture in team1_stats if fixture.fixture_id in team2_stats_fixture_ids]
        team2_stats = [fixture for fixture in team2_stats if fixture.fixture_id in team1_stats_fixture_ids]

        h2h_stats = {
            'team1': team1_stats,
            'team2': team2_stats
        }
        return h2h_stats



