from django.apps import AppConfig

from gameserver.games import *


IPD_NAME = "ItePrisDilGame"
IPD_LONG_NAME = "Iterative Prisoners' Dilemma Game"
IPD_PACKAGE_NAME = "iteprisonergame"
IPD_URL_TAG = "itepris"
IPD_PACKAGE_URL_NAMESPACE = "itepris_game"

IPD_ROUNDS = [168, 359, 306, 622, 319]
IPD_PAYOFFS = {("C", "C"): (-10, -10), ("C", "D"): (-25, 0), ("D", "C"): (0, -25), ("D", "D"): (-20, -20)}


class IteprisonergameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = IPD_PACKAGE_NAME

    is_game = True
    game_setting = GameSetting(
            name=IPD_NAME,
            long_name=IPD_LONG_NAME,
            package_name=IPD_PACKAGE_NAME,
            url_tag=IPD_URL_TAG,
            package_url_namespace=IPD_PACKAGE_URL_NAMESPACE,
    )

    def ready(self):
        INSTALLED_GAME_APPS.append(IPD_NAME)
        INSTALLED_GAMES_SETTING[IPD_NAME] = self.game_setting
        INSTALLED_GAMES_CHOICES.append((self.game_setting.name, self.game_setting.long_name))

