from typing import Optional

from buco_db_controller.models.team import Team


class Elo:
    def __init__(
            self,
            fixture_id: int,
            ht: Team,
            at: Team,
            ht_elo_before: int,
            at_elo_before: int,
            ht_elo_after: int,
            at_elo_after: int
    ):
        self.fixture_id: int = fixture_id
        self.ht: Team = ht
        self.at: Team = at
        self.ht_elo_before: int = ht_elo_before
        self.at_elo_before: int = at_elo_before
        self.ht_elo_after: int = ht_elo_after
        self.at_elo_after: int = at_elo_after

    @classmethod
    def from_dict(cls, response: dict) -> 'Elo':
        fixture_id = response['parameters']['fixture']
        data = response['data']

        return cls(
            fixture_id=fixture_id,
            ht=Team(team_id=data['home']['team']['id'], name=data['home']['team']['name']),
            at=Team(team_id=data['away']['team']['id'], name=data['away']['team']['name']),
            ht_elo_before=data['home']['statistics']['elo_before'],
            at_elo_before=data['away']['statistics']['elo_before'],
            ht_elo_after=data['home']['statistics']['elo_after'],
            at_elo_after=data['away']['statistics']['elo_after']
        )
