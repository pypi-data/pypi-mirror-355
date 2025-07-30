from buco_db_controller.models.team import Team


class TeamLineups:
    def __init__(self, team: Team, startXI: dict, substitutes: dict, formation: str):
        self.team: Team = team
        self.startXI: dict = startXI
        self.substitutes: dict = substitutes
        self.formation: str = formation

    @classmethod
    def from_dict(cls, data: dict) -> 'TeamLineups':
        return cls(
            team=Team(team_id=data['team']['id'], name=data['team']['name']),
            startXI=data['startXI'],
            substitutes=data['substitutes'],
            formation=data['formation']
        )
