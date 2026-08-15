from core.tests.helpers import make_game as _make_game


def make_itepris_game(session, *, url_tag="itep", name="IPD", **kwargs):
    return _make_game(
        session, game_type="iteprisonergame", url_tag=url_tag, name=name, **kwargs
    )


ALWAYS_COOPERATE = "0: C, 0, 0"
ALWAYS_DEFECT = "0: D, 0, 0"
TIT_FOR_TAT = "0: C, 0, 1\n1: D, 0, 1"
