from django.apps import AppConfig

from gameserver.games import *


NG_NAME = "NumbersGame"
NG_LONG_NAME = "Numbers Game"
NG_PACKAGE_NAME = "numbersgame"
NG_URL_TAG = "numbers"
NG_PACKAGE_URL_NAMESPACE = "numbers_game"


class NumbersgameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'numbersgame'

    is_game = True
    game_setting = GameSetting(
        name=NG_NAME,
        long_name=NG_LONG_NAME,
        package_name=NG_PACKAGE_NAME,
        url_tag=NG_URL_TAG,
        package_url_namespace=NG_PACKAGE_URL_NAMESPACE,
    )

    def ready(self):
        INSTALLED_GAME_APPS.append(NG_NAME)
        INSTALLED_GAMES_SETTING[NG_NAME] = self.game_setting
        INSTALLED_GAMES_CHOICES.append((self.game_setting.name, self.game_setting.long_name))
