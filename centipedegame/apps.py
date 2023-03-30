from django.apps import AppConfig

from gameserver.games import *


class CentipedegameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'centipedegame'

    is_game = True
    game_setting = GameSetting(
            name="CentipedeGame",
            long_name="Centipede Game",
            package_name="centipedegame",
            url_tag="centipede",
            package_url_namespace="centipede_game",
        )

    def ready(self):
        INSTALLED_GAME_APPS.append("CentipedeGame")
        INSTALLED_GAMES_SETTING["CentipedeGame"] = self.game_setting
        INSTALLED_GAMES_CHOICES.append((self.game_setting.name, self.game_setting.long_name))
