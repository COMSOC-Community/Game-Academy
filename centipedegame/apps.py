from gameserver.games import GameConfig

NAME = "centipedegame"
LONGNAME = "Centipede Game"
URL_TAG = "centipede"
PACKAGE_URL_NAMESPACE = "centipede_game"


class CentipedeGameConfig(GameConfig):
    name = NAME

    def __init__(self, app_name, app_module):
        super().__init__(
            app_name,
            app_module,
            LONGNAME,
            __package__,
            URL_TAG,
            PACKAGE_URL_NAMESPACE,
        )
