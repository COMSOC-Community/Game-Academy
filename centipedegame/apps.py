from django.apps import AppConfig

from gameserver.games import *

CENTI_NAME = "CentipedeGame"
CENTI_LONG_NAME = "Centipede Game"
CENTI_PACKAGE_NAME = "centipedegame"
CENTI_URL_TAG = "centipede"
CENTI_PACKAGE_URL_NAMESPACE = "centipede_game"


class CentipedegameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'centipedegame'

    is_game = True
    game_setting = GameSetting(
            name=CENTI_NAME,
            long_name=CENTI_LONG_NAME,
            package_name=CENTI_PACKAGE_NAME,
            url_tag=CENTI_URL_TAG,
            package_url_namespace=CENTI_PACKAGE_URL_NAMESPACE,
        )

    def ready(self):
        INSTALLED_GAME_APPS.append("CentipedeGame")
        INSTALLED_GAMES_SETTING["CentipedeGame"] = self.game_setting
        INSTALLED_GAMES_CHOICES.append((self.game_setting.name, self.game_setting.long_name))
