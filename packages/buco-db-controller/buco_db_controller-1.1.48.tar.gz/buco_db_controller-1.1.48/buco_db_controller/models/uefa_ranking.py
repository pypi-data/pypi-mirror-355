

class UEFARanking:
    def __init__(self, season: int, coefficients: dict):
        self.season: int = season
        self.coefficients: dict = coefficients

    @classmethod
    def from_dict(cls, response: dict) -> 'UEFARanking':
        return cls(season=response['parameters']['season'], coefficients=response['data'])
