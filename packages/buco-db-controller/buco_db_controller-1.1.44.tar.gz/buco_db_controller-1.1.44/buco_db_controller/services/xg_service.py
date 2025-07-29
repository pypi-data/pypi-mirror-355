from buco_db_controller.models.xg import XG
from buco_db_controller.repositories.xg_repository import XGRepository
from buco_db_controller.services.fixture_service import FixtureService


class XGService:
    fbref = 'fbref'
    understat = 'understat'
    flashscore = 'flashscore'

    def __init__(self):
        self.fbref_xg_repository = XGRepository(self.fbref)
        self.understat_xg_repository = XGRepository(self.understat)
        self.flashscore_xg_repository = XGRepository(self.flashscore)
        self.fixture_service = FixtureService()

    def upsert_many_fixture_xg(self, xg: list[dict], source: str):
        if source == self.fbref:
            self.fbref_xg_repository.upsert_many_fixture_xg(xg)
        elif source == self.understat:
            self.understat_xg_repository.upsert_many_fixture_xg(xg)
        elif source == self.flashscore:
            self.flashscore_xg_repository.upsert_many_fixture_xg(xg)

    def get_xg(self, fixture_id: int) -> XG:
        xg = self._get_prioritized_xg([fixture_id])[0]
        return xg

    def get_xg_over_season(self, team_id: int, league_id: int, season: int, prior: bool = True) -> list[XG]:
        fixture_ids = self.fixture_service.get_fixture_ids(team_id, league_id, season)

        if prior:
            return self._get_prioritized_xg(fixture_ids)
        else:
            return self._get_average_xg(fixture_ids)

    def get_h2h_xg(self, team1_id: int, team2_id: int, league_id: int, season: int, prior: bool = True) -> list[XG]:
        h2h_fixture_ids = self.fixture_service.get_h2h_fixture_ids(team1_id, team2_id, league_id, season)
        if prior:
            return self._get_prioritized_xg(h2h_fixture_ids)
        else:
            return self._get_average_xg(h2h_fixture_ids)

    def _get_prioritized_xg(self, fixture_ids: list[int]) -> list[XG]:
        xg_data = {
            self.fbref: [XG.from_dict(x) for x in self.fbref_xg_repository.get_many_xg(fixture_ids)],
            self.understat: [XG.from_dict(x) for x in self.understat_xg_repository.get_many_xg(fixture_ids)],
            self.flashscore: [XG.from_dict(x) for x in self.flashscore_xg_repository.get_many_xg(fixture_ids)],
        }

        prioritized_xg = []
        for fixture_id in fixture_ids:
            for source in [self.fbref, self.understat, self.flashscore]:
                xgoal = next((x for x in xg_data[source] if x.fixture_id == fixture_id), None)
                if xgoal and xgoal.ht_xg and xgoal.at_xg:
                    prioritized_xg.append(xgoal)
                    break

        return prioritized_xg

    def _get_average_xg(self, fixture_ids: list[int]) -> list[XG]:
        xg_data = {
            self.fbref: [XG.from_dict(x) for x in self.fbref_xg_repository.get_many_xg(fixture_ids)],
            self.understat: [XG.from_dict(x) for x in self.understat_xg_repository.get_many_xg(fixture_ids)],
            self.flashscore: [XG.from_dict(x) for x in self.flashscore_xg_repository.get_many_xg(fixture_ids)],
        }

        avg_xgs = []
        for fixture_id in fixture_ids:
            home_xgs = []
            away_xgs = []
            ht = at = ht_goals = at_goals = None

            for source in xg_data:
                xg = next((x for x in xg_data[source] if x.fixture_id == fixture_id), None)
                if xg:
                    # Collecting xg values
                    if xg.ht_xg is not None:
                        home_xgs.append(xg.ht_xg)
                    if xg.at_xg is not None:
                        away_xgs.append(xg.at_xg)

                    # Collecting other data (assuming consistency across sources)
                    ht = xg.ht or ht
                    at = xg.at or at
                    ht_goals = xg.ht_goals if ht_goals is None else ht_goals
                    at_goals = xg.at_goals if at_goals is None else at_goals

            if home_xgs and away_xgs and ht and at:
                avg_xg = XG(
                    fixture_id=fixture_id,
                    ht=ht,
                    at=at,
                    ht_xg=sum(home_xgs) / len(home_xgs),
                    at_xg=sum(away_xgs) / len(away_xgs),
                    ht_goals=ht_goals,
                    at_goals=at_goals
                )
                avg_xgs.append(avg_xg)

        return avg_xgs
