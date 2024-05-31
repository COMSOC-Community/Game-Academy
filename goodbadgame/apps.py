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
            management_commands=["goodbad_generatejsgraphdata"],
            answer_model_fields=("score", ),
            illustration_paths=("img/goodbad1.png", "img/goodbad2.png", "img/goodbad3.png", "img/goodbad4.png"),
        )

    def ready(self):
        super(GoodBadGameConfig, self).ready()

        from goodbadgame.models import Setting, Answer
        from goodbadgame.forms import SettingForm

        self.register_models(Setting, SettingForm, Answer)
