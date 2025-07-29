from buco_db_controller.models.league import League


class TeamStats:
    def __init__(
            self,
            fixture_id: int,
            season: int,
            date: str,
            league: League,
            league_round: str,
            team_id: int,
            team_stats: dict
    ):
        self.fixture_id: int = fixture_id
        self.date: str = date
        self.season: int = season
        self.team_id: int = team_id
        self.league: League = league
        self.league_round: str = league_round
        self.team_stats: dict = team_stats

    @classmethod
    def from_dict(cls, response: dict) -> 'TeamStats':
        fixture_id = response['parameters']['fixture']
        date = response['parameters']['date']
        season = response['parameters']['season']
        league_round = response['parameters']['round']
        team_id = response['parameters']['team']

        data = response['data']

        return cls(
            fixture_id=fixture_id,
            season=season,
            date=date,
            league=League(league_id=data['league']['id'], name=data['league']['name']),
            league_round=league_round,
            team_id=team_id,
            team_stats=data,
        )
