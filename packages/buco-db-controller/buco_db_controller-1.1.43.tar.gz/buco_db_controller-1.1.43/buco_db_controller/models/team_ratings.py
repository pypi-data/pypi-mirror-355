

class TeamRatings:
    def __init__(self, season: int, team_ratings: dict):
        self.season: int = season
        self.team_ratings: dict = team_ratings

    @classmethod
    def from_dict(cls, response: dict) -> 'TeamRatings':
        season = response['parameters']['season']
        team_ratings = response['data']

        return cls(season=season, team_ratings=team_ratings)
