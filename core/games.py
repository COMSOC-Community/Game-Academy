from django.apps import AppConfig


class GameConfig(AppConfig):
    def __init__(
        self,
        app_name,
        app_module,
        long_name,
        package_name,
        url_tag,
        url_namespace,
        setting_cls=None,
        setting_form=None,
    ):
        super().__init__(app_name, app_module)
        self.is_game = True

        self.name = app_name
        self.long_name = long_name
        self.package_name = package_name
        self.url_tag = url_tag
        self.url_namespace = url_namespace
        self.setting_cls = setting_cls
        self.setting_form = setting_form

    def ready(self):
        INSTALLED_GAMES.append(self)
        INSTALLED_GAMES_CHOICES.append((self.name, self.long_name))
        self.extra_ready()

    def extra_ready(self):
        pass


INSTALLED_GAMES = []
INSTALLED_GAMES_CHOICES = []
