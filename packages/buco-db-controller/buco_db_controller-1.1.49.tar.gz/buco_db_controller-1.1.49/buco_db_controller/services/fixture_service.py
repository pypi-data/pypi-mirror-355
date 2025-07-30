from typing import List, Optional, Union

from buco_db_controller.models.fixture import Fixture
from buco_db_controller.repositories.fixture_repository import FixtureRepository, logger


class FixtureService:

    def __init__(self):
        self.fixture_repository = FixtureRepository()

    def upsert_many_fixtures(self, fixtures: List[dict]):
        self.fixture_repository.upsert_many_fixtures(fixtures)

    def upsert_many_fixtures_before(self, fixtures: List[dict]):
        self.fixture_repository.upsert_many_fixtures_before(fixtures)

    def get_team_fixtures(self, team_id: int, league_id: int, seasons: Union[int, List[int]]) -> List[Fixture]:
        response = self.fixture_repository.get_team_fixtures(team_id, league_id, seasons)
        fixtures_data = [fixture for team in response for fixture in team.get('data', [])]
        fixtures_data = list({fixture['fixture']['id']: fixture for fixture in fixtures_data}.values())

        if not fixtures_data:
            logger.error(f'No fixtures found for team {team_id}, league {league_id} and season {seasons}')
            return []

        fixtures = [Fixture.from_dict(team) for team in fixtures_data]
        fixtures.sort(key=lambda x: x.datetime)

        fixtures = [fixture for fixture in fixtures if 'Relegation' not in fixture.league_round]
        return fixtures

    def get_league_fixtures(self, league_id: int, seasons: Union[int, List[int]]) -> List[Fixture]:
        response = self.fixture_repository.get_league_fixtures(league_id, seasons)
        fixtures_data = [fixture for team in response for fixture in team.get('data', [])]
        fixtures_data = list({fixture['fixture']['id']: fixture for fixture in fixtures_data}.values())

        if not fixtures_data:
            logger.error(f'No fixtures found league {league_id} and season {seasons}')
            return []

        fixtures = [Fixture.from_dict(team) for team in fixtures_data]
        fixtures.sort(key=lambda x: (x.datetime, x.fixture_id))
        return fixtures

    def get_fixture_ids(self, team_id: int, league_id: int, seasons: Union[int, List[int]]) -> List[int]:
        seasons = [seasons] if isinstance(seasons, int) else seasons
        fixtures = self.get_team_fixtures(team_id, league_id, seasons)
        fixture_ids = [fixture.fixture_id for fixture in fixtures]
        fixture_ids.sort()
        return fixture_ids

    def get_league_fixture_ids(self, league_id: int, seasons: Union[int, List[int]]) -> list:
        seasons = [seasons] if isinstance(seasons, int) else seasons
        fixtures = self.get_league_fixtures(league_id, seasons)
        fixture_ids = [fixture.fixture_id for fixture in fixtures]
        fixture_ids.sort()
        return fixture_ids

    def get_fixture_dates(self, team_id: int, league_id: int, season: int) -> list:
        fixtures = self.get_team_fixtures(team_id, league_id, season)
        fixture_dates = [fixture.datetime for fixture in fixtures]
        return fixture_dates

    def get_nth_round_fixture(self, league_round: str, team_id: int, league_id: int, season: int) -> Optional[Fixture]:
        fixtures = self.get_team_fixtures(team_id, league_id, season)

        if fixtures is None:
            logger.warn(f'No fixtures found for team {team_id} | league {league_id} | season {season}')
            return None

        for fixture in fixtures:
            if fixture.league_round == league_round:
                return fixture

        logger.warn(f'No fixture found for round {league_round} | team {team_id} | league {league_id} | season {season}')
        return None

    def upsert_many_rounds(self, league_rounds: list):
        self.fixture_repository.upsert_many_rounds(league_rounds)

    def get_league_rounds_count(self, league_id: int, season: int) -> int:
        league_rounds = self.fixture_repository.get_rounds(league_id, season)
        league_rounds = [league_round for league_round in league_rounds['data'] if 'Regular Season' in league_round]
        return len(league_rounds)

    def get_league_rounds(self, league_id: int, season: int) -> list:
        league_rounds = self.fixture_repository.get_rounds(league_id, season)
        league_rounds = [league_round for league_round in league_rounds['data'] if 'Regular Season' in league_round]
        return league_rounds

    def get_h2h_fixtures(self, team1_id: int, team2_id: int, league_id: int, seasons: Union[int, List[int]]) -> List[Fixture]:
        team1_fixtures = self.get_team_fixtures(team1_id, league_id, seasons)
        team2_fixtures = self.get_team_fixtures(team2_id, league_id, seasons)
        teams_fixtures = team1_fixtures + team2_fixtures
        fixtures = []

        for team_fixtures in teams_fixtures:
            fixtures.extend([Fixture.from_dict(fixture) for fixture in team_fixtures.get('data', [])])

        h2h_fixtures = fixtures.copy()
        for fixture in fixtures:
            if fixture.ht.team_id not in [team1_id, team2_id] or fixture.at.team_id not in [team1_id, team2_id]:
                h2h_fixtures.remove(fixture)

        h2h_fixtures = list({fixture.fixture_id: fixture for fixture in h2h_fixtures}.values())
        h2h_fixtures.sort(key=lambda x: x.datetime)
        return h2h_fixtures

    def get_h2h_fixture_ids(self, team1_id: int, team2_id: int, league_id: int, seasons: Union[int, List[int]]) -> List[int]:
        team1_fixtures = self.get_team_fixtures(team1_id, league_id, seasons)
        team2_fixtures = self.get_team_fixtures(team2_id, league_id, seasons)
        teams_fixtures = team1_fixtures + team2_fixtures
        fixture_ids = [fixture.fixture_id for fixture in teams_fixtures]
        return fixture_ids

    def get_previous_team_fixtures(self, fixture: Fixture) -> tuple[Optional[Fixture], Optional[Fixture]]:
        """
        Retrieve the most recent previous fixtures for both the home and away teams
        before the given fixture's datetime.

        The search includes fixtures from the current season and the previous season.
        If no previous fixture exists for a team, None is returned for that team.

        Args:
        fixture (Fixture): The fixture for which previous fixtures are being retrieved.

        Returns:
        tuple[Optional[Fixture], Optional[Fixture]]:
        A tuple containing:
        - The most recent previous fixture for the home team (or None).
        - The most recent previous fixture for the away team (or None).
        """
        seasons = [fixture.season, fixture.season - 1]
        ht_fixtures = self.get_team_fixtures(fixture.ht.team_id, fixture.league.league_id, seasons)
        at_fixtures = self.get_team_fixtures(fixture.at.team_id, fixture.league.league_id, seasons)
        ht_fixtures = [f for f in ht_fixtures if f.datetime < fixture.datetime]
        at_fixtures = [f for f in at_fixtures if f.datetime < fixture.datetime]

        ht_prev_fixture = None
        at_prev_fixture = None
        if ht_fixtures:
            ht_prev_fixture = ht_fixtures[-1]
        if at_fixtures:
            at_prev_fixture = at_fixtures[-1]

        return ht_prev_fixture, at_prev_fixture
