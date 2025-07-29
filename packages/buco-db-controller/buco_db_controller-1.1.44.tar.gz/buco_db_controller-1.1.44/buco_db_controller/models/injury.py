from buco_db_controller.models.league import League
from buco_db_controller.models.team import Team


class Injury:
    def __init__(
            self,
            player_id: int,
            player_name: str,
            team: Team,
            fixture_id: int,
            fixture_date: str,
            league: League
    ):
        self.player_id: int = player_id
        self.player_name: str = player_name
        self.team: Team = team
        self.fixture_id: int = fixture_id
        self.fixture_date = fixture_date
        self.league: League = league

    @classmethod
    def from_dict(cls, response: dict) -> 'Injury':
        data = response['data']
        return cls(
            player_id=data['player']['id'],
            player_name=data['player']['name'],
            team=Team(team_id=data['team']['id'], name=data['team']['name']),
            fixture_id=data['fixture']['id'],
            fixture_date=data['fixture']['date'],
            league=League(
                league_id=data['league']['id'],
                name=data['league']['name'],
                country=data['league']['country']
            )
        )
