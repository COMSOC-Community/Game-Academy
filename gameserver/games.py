from django.apps import AppConfig


class GameConfig(AppConfig):
    def __init__(
        self,
        app_name,
        app_module,
        long_name,
        package_name,
        package_url_namespace,
        url_tag,
    ):
        super().__init__(app_name, app_module)
        self.is_game = True
        self.long_name = long_name
        self.package_name = package_name
        self.package_url_namespace = package_url_namespace
        self.url_tag = url_tag
        self.game_setting = GameSetting(
            name=self.name,
            long_name=self.long_name,
            package_name=self.package_name,
            url_tag=self.url_tag,
            package_url_namespace=self.package_url_namespace,
        )

    def ready(self):
        INSTALLED_GAME_APPS.append(self.game_setting.name)
        INSTALLED_GAMES_SETTING[self.game_setting.name] = self.game_setting
        INSTALLED_GAMES_CHOICES.append(
            (self.game_setting.name, self.game_setting.long_name)
        )


class GameSetting:
    def __init__(self, name, long_name, package_name, package_url_namespace, url_tag):
        self.name = name
        self.long_name = long_name
        self.package_name = package_name
        self.package_url_namespace = package_url_namespace
        self.url_tag = url_tag


INSTALLED_GAME_APPS = []
INSTALLED_GAMES_SETTING = {}
INSTALLED_GAMES_CHOICES = []
