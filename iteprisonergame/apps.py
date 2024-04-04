from core.games import GameConfig

NAME = "iteprisonergame"
LONGNAME = "Iterative Prisoner's Dilemma Game"
URL_TAG = "itepris"
URL_NAMESPACE = "itepris_game"


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
            management_commands=["ipd_computeresults", "ipd_generategraphdata"],
            answer_model_fields=("name", "avg_score", "motivation"),
            illustration_paths=("img/IPD1.png", "img/IPD2.png", "img/IPD3.png"),
        )

    def ready(self):
        super(ItePrisonerGameConfig, self).ready()

        from iteprisonergame.models import Setting, Answer
        from iteprisonergame.forms import SettingForm

        self.register_models(Setting, SettingForm, Answer)
