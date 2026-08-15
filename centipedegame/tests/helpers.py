from core.tests.helpers import make_game as _make_game


def make_centipede_game(session, *, url_tag="centi", name="Centipede", **kwargs):
    return _make_game(
        session, game_type="centipedegame", url_tag=url_tag, name=name, **kwargs
    )
