from django.apps import AppConfig

from core.games import GameConfig

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
            answer_model_fields=("score", ),
            illustration_paths=("goodbad/img/goodbad1.png", "goodbad/img/goodbad2.png", "goodbad/img/goodbad3.png", "goodbad/img/goodbad4.png"),
        )

    def ready(self):
        from goodbadgame.models import Setting, Answer
        from goodbadgame.forms import SettingForm

        self.register_models(Setting, SettingForm, Answer)

        super(GoodBadGameConfig, self).ready()
