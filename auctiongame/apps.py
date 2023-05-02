from django.apps import AppConfig

from gameserver.games import *

AUCT_NAME = "AuctionGame"
AUCT_LONG_NAME = "Auction Game"
AUCT_PACKAGE_NAME = "auctiongame"
AUCT_URL_TAG = "auction"
AUCT_PACKAGE_URL_NAMESPACE = "auction_game"


class AuctiongameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = AUCT_PACKAGE_NAME

    is_game = True
    game_setting = GameSetting(
            name=AUCT_NAME,
            long_name=AUCT_LONG_NAME,
            package_name=AUCT_PACKAGE_NAME,
            url_tag=AUCT_URL_TAG,
            package_url_namespace=AUCT_PACKAGE_URL_NAMESPACE,
        )

    def ready(self):
        INSTALLED_GAME_APPS.append("AuctionGame")
        INSTALLED_GAMES_SETTING["AuctionGame"] = self.game_setting
        INSTALLED_GAMES_CHOICES.append((self.game_setting.name, self.game_setting.long_name))
