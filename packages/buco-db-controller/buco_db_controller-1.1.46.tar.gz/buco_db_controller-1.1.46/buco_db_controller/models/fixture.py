from datetime import datetime as dt

from buco_db_controller.models.league import League
from buco_db_controller.models.team import Team


class Fixture:
    def __init__(
            self,
            fixture_id: int,
            datetime: str,
            status: dict,
            season: int,
            league: League,
            league_round: str,
            ht: Team,
            ht_winner: bool,
            at: Team,
            at_winner: bool,
            ft_goals: dict,
            mt_goals: dict
    ):
        self.fixture_id: int = fixture_id
        self.datetime: dt = dt.fromisoformat(datetime)
        self.status: dict = status

        self.season: int = season
        self.league: League = league
        self.league_round: str = league_round

        self.ht: Team = ht
        self.ht_winner: bool = ht_winner

        self.at: Team = at
        self.at_winner: bool = at_winner

        self.ft_goals: dict = ft_goals
        self.mt_goals: dict = mt_goals

    @classmethod
    def from_dict(cls, data: dict) -> 'Fixture':
        return cls(
            fixture_id=data['fixture']['id'],
            datetime=data['fixture']['date'],
            status=data['fixture']['status'],
            season=data['league']['season'],
            league=League(
                league_id=data['league']['id'],
                name=data['league']['name'],
                country=data['league']['country']
            ),
            league_round=data['league']['round'],
            ht=Team(team_id=data['teams']['home']['id'], name=data['teams']['home']['name']),
            ht_winner=data['teams']['home']['winner'],
            at=Team(team_id=data['teams']['away']['id'], name=data['teams']['away']['name']),
            at_winner=data['teams']['away']['winner'],
            ft_goals=data['score']['fulltime'],
            mt_goals=data['score']['halftime'],
        )

    def get_date(self) -> str:
        return self.datetime.isoformat().split('T')[0]
