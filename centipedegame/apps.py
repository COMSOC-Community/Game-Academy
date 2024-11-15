from core.game_config import GameConfig

NAME = "centipedegame"
LONGNAME = "Centipede Game"
URL_TAG = "centipede"
URL_NAMESPACE = "centipede_game"


class CentipedeGameConfig(GameConfig):
    name = NAME

    def __init__(self, app_name, app_module):
        super().__init__(
            app_name,
            app_module,
            LONGNAME,
            __package__,
            URL_TAG,
            URL_NAMESPACE,
            management_commands="centi_computescores",
            answer_model_fields=("strategy_as_p1", "strategy_as_p2", "motivation"),
            illustration_paths=(
                "centipedegame/img/CentipedeGame1.png",
                "centipedegame/img/CentipedeGame2.png",
                "centipedegame/img/CentipedeGame3.png",
                "centipedegame/img/CentipedeGame4.png",
            ),
        )

    def ready(self):
        from centipedegame.models import Answer, Setting
        from centipedegame.forms import SettingForm

        self.register_models(
            setting_model=Setting, setting_form=SettingForm, answer_model=Answer
        )

        from centipedegame.exportdata import answers_to_csv, settings_to_csv

        self.answer_to_csv_func = answers_to_csv
        self.settings_to_csv_func = settings_to_csv

        from centipedegame.random import create_random_answers

        self.random_answers_func = create_random_answers

        super(CentipedeGameConfig, self).ready()
