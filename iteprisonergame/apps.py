from gameserver.games import GameConfig

NAME = "iteprisonergame"
LONGNAME = "Iterative Prisoners' Dilemma Game"
URL_TAG = "itepris"
URL_NAMESPACE = "itepris_game"

IPD_ROUNDS = [168, 359, 306, 622, 319]
IPD_PAYOFFS = {
    ("C", "C"): (-10, -10),
    ("C", "D"): (-25, 0),
    ("D", "C"): (0, -25),
    ("D", "D"): (-20, -20),
}


class ItePrisonerGameConfig(GameConfig):
    name = NAME

    def __init__(self, app_name, app_module):
        super().__init__(
            app_name,
            app_module,
            LONGNAME,
            __package__,
            URL_TAG,
            URL_NAMESPACE,
        )
