from core.game_config import GameConfig

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
            illustration_paths=(
                "iteprisonergame/img/IPD1.png",
                "iteprisonergame/img/IPD2.png",
                "iteprisonergame/img/IPD3.png",
            ),
        )

    def ready(self):
        from iteprisonergame.models import Setting, Answer
        from iteprisonergame.forms import SettingForm

        self.register_models(Setting, SettingForm, Answer)

        from iteprisonergame.exportdata import answers_to_csv, settings_to_csv

        self.answer_to_csv_func = answers_to_csv
        self.settings_to_csv_func = settings_to_csv

        from iteprisonergame.random import create_random_answers

        self.random_answers_func = create_random_answers

        super(ItePrisonerGameConfig, self).ready()
