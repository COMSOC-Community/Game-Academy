from core.game_config import GameConfig

NAME = "goodbadgame"
LONGNAME = "Good or Bad Game"
URL_TAG = "goodbad"
URL_NAMESPACE = "goodbad_game"


class GoodBadGameConfig(GameConfig):
    name = NAME

    def __init__(self, app_name, app_module):
        super().__init__(
            app_name,
            app_module,
            LONGNAME,
            __package__,
            URL_TAG,
            URL_NAMESPACE,
            management_commands=["goodbad_computeresults"],
            update_management_commands=["goodbad_updateresults"],
            answer_model_fields=("score",),
            illustration_paths=(
                "goodbad/img/goodbad1.png",
                "goodbad/img/goodbad2.png",
                "goodbad/img/goodbad3.png",
                "goodbad/img/goodbad4.png",
            ),
        )

    def ready(self):
        from goodbadgame.models import Setting, Answer
        from goodbadgame.forms import SettingForm

        self.register_models(Setting, SettingForm, Answer)

        from goodbadgame.exportdata import answers_to_csv, settings_to_csv

        self.answer_to_csv_func = answers_to_csv
        self.settings_to_csv_func = settings_to_csv

        from goodbadgame.random import create_random_answers

        self.random_answers_func = create_random_answers

        super(GoodBadGameConfig, self).ready()
