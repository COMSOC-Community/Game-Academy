from core.games import GameConfig

NAME = "numbersgame"
LONGNAME = "Numbers Game"
URL_TAG = "numbers"
URL_NAMESPACE = "numbers_game"


class NumbersGameConfig(GameConfig):
    name = NAME

    def __init__(self, app_name, app_module):
        super().__init__(
            app_name,
            app_module,
            LONGNAME,
            __package__,
            URL_TAG,
            URL_NAMESPACE,
            management_commands="ng_results"
        )

    def ready(self):
        super(NumbersGameConfig, self).ready()

        from numbersgame.models import Setting
        from numbersgame.forms import SettingForm
        self.register_setting_objects(Setting, SettingForm)
