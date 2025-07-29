
class League:
    def __init__(self, league_id: int, name: str, country: str = None):
        self.league_id: int = league_id
        self.name: str = name
        self.country: str = country

    @classmethod
    def from_dict(cls, response: dict) -> 'League':
        data = response['data']
        return cls(
            league_id=data[-1]['league']['id'],
            name=data[-1]['league']['name'],
            country=data[-1]['country']['name']
        )
