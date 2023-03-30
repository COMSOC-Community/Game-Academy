from django.apps import AppConfig

from gameserver.games import *


class IteprisonergameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iteprisonergame'

    is_game = True
    game_setting = GameSetting(
            name="ItePrisDilGame",
            long_name="Iterative Prisoners' Dilemma Game",
            package_name="iteprisonergame",
            url_tag="itepris",
            package_url_namespace="itepris_game",
    )

    def ready(self):
        INSTALLED_GAME_APPS.append("ItePrisDilGame")
        INSTALLED_GAMES_SETTING["ItePrisDilGame"] = self.game_setting
        INSTALLED_GAMES_CHOICES.append((self.game_setting.name, self.game_setting.long_name))

