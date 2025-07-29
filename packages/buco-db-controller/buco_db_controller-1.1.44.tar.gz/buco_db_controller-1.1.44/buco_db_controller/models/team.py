

class Team:
    def __init__(self, team_id: int, name: str, country: str = None):
        self.team_id: int = team_id
        self.name: str = name
        self.country: str = country

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create a Team object from a dictionary.
        """
        return cls(
            team_id=data['team']['id'],
            name=data['team']['name'],
            country=data['team']['country']
        )
