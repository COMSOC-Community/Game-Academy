from django.apps import AppConfig

from gameserver.games import *


class AuctiongameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auctiongame'

    is_game = True
    game_setting = GameSetting(
            name="AuctionGame",
            long_name="Auction Game",
            package_name="auctiongame",
            url_tag="auction",
            package_url_namespace="auction_game",
        )

    def ready(self):
        INSTALLED_GAME_APPS.append("AuctionGame")
        INSTALLED_GAMES_SETTING["AuctionGame"] = self.game_setting
        INSTALLED_GAMES_CHOICES.append((self.game_setting.name, self.game_setting.long_name))
