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
            answer_model_fields=("probabilities_as_tuple", "round_robin_position", "best_response", "motivation"),
            illustration_paths=("simp_poker/img/SimpPoker1.png", "simp_poker/img/SimpPoker2.png"),
        )

    def ready(self):
        super(SimpPokerConfig, self).ready()

        from simp_poker.models import Setting, Answer

        # from simp_poker.forms import SettingForm
        self.register_models(Setting, None, Answer)
