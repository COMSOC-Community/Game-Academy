from core.tests.helpers import make_game as _make_game


def make_poker_game(session, *, url_tag="pokr", name="Poker", **kwargs):
    return _make_game(
        session, game_type="simp_poker", url_tag=url_tag, name=name, **kwargs
    )
