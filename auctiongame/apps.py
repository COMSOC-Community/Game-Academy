from core.games import GameConfig

NAME = "auctiongame"
LONGNAME = "Auction Game"
URL_TAG = "auction"
URL_NAMESPACE = "auction_game"


class AuctionGameConfig(GameConfig):
    name = NAME

    def __init__(self, app_name, app_module):
        super().__init__(
            app_name,
            app_module,
            LONGNAME,
            __package__,
            URL_TAG,
            URL_NAMESPACE,
        )
