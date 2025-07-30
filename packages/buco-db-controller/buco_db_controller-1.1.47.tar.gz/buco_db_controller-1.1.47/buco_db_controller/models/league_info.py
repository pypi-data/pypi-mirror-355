from datetime import datetime

import unidecode


class LeagueInfo:
    def __init__(self, league_id: int, league_name: str, league_type: str = None,
                 country_code: str = None, country_name: str = None, seasons: list = None,
                 start: datetime = None, end: datetime = None):
        self.league_id: int = league_id
        self.league_name: str = league_name
        self.league_type: str = league_type

        self.country_code: str = country_code
        self.country_name: str = country_name

        self.seasons: list = seasons

        self.league_name_unicode = unidecode.unidecode(league_name.lower().replace(' ', '_'))
        self.country_name_unicode = unidecode.unidecode(country_name.lower().replace(' ', '_'))
        self.league_country_name_unicode: str = f'{self.league_name_unicode}_{self.country_name_unicode}'

        self.start = start
        self.end = end

    @classmethod
    def from_dict(cls, response: dict) -> 'LeagueInfo':
        data = response['data']

        return cls(
            league_id=data['league']['id'],
            league_name=data['league']['name'],
            league_type=data['league'].get('type'),
            country_code=data['country'].get('code'),
            country_name=data['country'].get('name'),
            seasons=data.get('seasons', []),
            start=datetime.strptime(data.get('start'), '%Y-%m-%d'),
            end=datetime.strptime(data.get('end'), '%Y-%m-%d')
        )

