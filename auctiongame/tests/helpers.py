from core.tests.helpers import make_game as _make_game


def make_auction_game(session, *, url_tag="auct", name="Auction", **kwargs):
    return _make_game(
        session, game_type="auctiongame", url_tag=url_tag, name=name, **kwargs
    )
