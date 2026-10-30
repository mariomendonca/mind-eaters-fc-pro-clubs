import pytest

from app import ea
from app.config import Settings
from app.ea import LiveEASource
from tests.factories import make_bundle

SETTINGS = Settings()
REF = make_bundle()


class StubAPI:
    matches_value = "default"

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def search_club_by_name(self, name, scope="all_time"):
        assert scope == "current_season"
        return [{"clubId": 555, "clubName": "Mind Eaters FC II"}, REF.season]

    def get_club_overall_stats(self, club_id):
        return [REF.overall]

    def get_member_stats(self, club_id):
        return REF.members

    def get_club_matches(self, club_id, match_type="leagueMatch", count=10, output=None):
        if StubAPI.matches_value is None:
            return None
        if output == "raw":
            return REF.raw_matches
        return REF.matches

    def get_match_players(self, club_id, match_type="leagueMatch", count=10):
        if StubAPI.matches_value is None:
            return None
        return REF.match_players

    def get_club_details(self, club_id):
        return [REF.details]


@pytest.fixture
def stub_api(monkeypatch):
    StubAPI.matches_value = "default"
    monkeypatch.setattr(ea, "FC27API", StubAPI)
    return StubAPI


def test_fetch_picks_our_club_from_season_search(stub_api):
    b = LiveEASource(SETTINGS, sleep=lambda s: None).fetch(include_details=False)
    assert b.season["clubId"] == 1232878
    assert b.overall["skillRating"] == 1782
    assert len(b.members) == len(REF.members)
    assert b.fetched_at.tzinfo is not None


def test_null_matches_become_empty(stub_api):
    stub_api.matches_value = None
    b = LiveEASource(SETTINGS, sleep=lambda s: None).fetch(include_details=False)
    assert b.matches == [] and b.match_players == [] and b.raw_matches == []


def test_sleeps_between_calls(stub_api):
    sleeps = []
    LiveEASource(SETTINGS, sleep=sleeps.append).fetch(include_details=False)
    assert len(sleeps) >= 5 and all(s == 1 for s in sleeps)


def test_details_only_when_requested(stub_api):
    src = LiveEASource(SETTINGS, sleep=lambda s: None)
    assert src.fetch(include_details=False).details is None
    assert src.fetch(include_details=True).details["stadium"] == "Estádio de ní"


def test_missing_club_in_search_gives_none(stub_api, monkeypatch):
    monkeypatch.setattr(StubAPI, "search_club_by_name", lambda self, name, scope="all_time": [])
    assert LiveEASource(SETTINGS, sleep=lambda s: None).fetch(include_details=False).season is None
