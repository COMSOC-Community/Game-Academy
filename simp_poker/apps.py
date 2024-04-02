from core.games import GameConfig

NAME = "simp_poker"
LONGNAME = "Simplified Poker"
URL_TAG = "poker"
URL_NAMESPACE = "simp_poker"


class SimpPokerConfig(GameConfig):
    name = NAME

    def __init__(self, app_name, app_module):
        super().__init__(
            app_name,
            app_module,
            LONGNAME,
            __package__,
            URL_TAG,
            URL_NAMESPACE,
            management_commands="simppoker_computeresults",
            answer_model_fields=("avg_score",),
            illustration_path="img/SimpPoker.png",
        )

    def ready(self):
        super(SimpPokerConfig, self).ready()

        from simp_poker.models import Setting, Answer

        # from simp_poker.forms import SettingForm
        self.register_models(Setting, None, Answer)
