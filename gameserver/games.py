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
