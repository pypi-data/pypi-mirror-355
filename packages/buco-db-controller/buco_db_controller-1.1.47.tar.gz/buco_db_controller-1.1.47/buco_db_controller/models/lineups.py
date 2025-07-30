from buco_db_controller.models.team_lineups import TeamLineups


class Lineups:
    def __init__(self, fixture_id: int, ht_lineup: TeamLineups, at_lineup: TeamLineups):
        self.fixture_id: int = fixture_id
        self.ht_lineup: TeamLineups = ht_lineup
        self.at_lineup: TeamLineups = at_lineup

    @classmethod
    def from_dict(cls, response: dict) -> 'Lineups':
        fixture_id = response['parameters']['fixture']
        data = response['data']

        ht_injuries = TeamLineups.from_dict(data[0])
        at_injuries = TeamLineups.from_dict(data[1])

        return cls(fixture_id=fixture_id, ht_lineup=ht_injuries, at_lineup=at_injuries)
