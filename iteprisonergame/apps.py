from django.apps import AppConfig

from gameserver.games import *


IP_NAME = "ItePrisDilGame"
IP_LONG_NAME = "Iterative Prisoners' Dilemma Game"
IP_PACKAGE_NAME = "iteprisonergame"
IP_URL_TAG = "itepris"
IP_PACKAGE_URL_NAMESPACE = "itepris_game"


class IteprisonergameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iteprisonergame'

    is_game = True
    game_setting = GameSetting(
            name=IP_NAME,
            long_name=IP_LONG_NAME,
            package_name=IP_PACKAGE_NAME,
            url_tag=IP_URL_TAG,
            package_url_namespace=IP_PACKAGE_URL_NAMESPACE,
    )

    def ready(self):
        INSTALLED_GAME_APPS.append("ItePrisDilGame")
        INSTALLED_GAMES_SETTING["ItePrisDilGame"] = self.game_setting
        INSTALLED_GAMES_CHOICES.append((self.game_setting.name, self.game_setting.long_name))

