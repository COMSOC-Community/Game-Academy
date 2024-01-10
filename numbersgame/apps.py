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
        )

    def extra_ready(self):
        from numbersgame.models import Setting
        from numbersgame.forms import SettingForm

        self.setting_cls = Setting
        self.setting_form = SettingForm
