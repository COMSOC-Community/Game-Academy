from django.apps import AppConfig

from gameserver.games import *


class NumbersgameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'numbersgame'

    is_game = True
    game_setting = GameSetting(
        name="NumbersGame",
        long_name="Numbers Game",
        package_name="numbersgame",
        url_tag="numbers",
        package_url_namespace="numbers_game",
    )

    def ready(self):
        INSTALLED_GAME_APPS.append("NumbersGame")
        INSTALLED_GAMES_SETTING["NumbersGame"] = self.game_setting
        INSTALLED_GAMES_CHOICES.append((self.game_setting.name, self.game_setting.long_name))
