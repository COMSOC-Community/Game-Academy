from collections.abc import Iterable

from django.apps import AppConfig

from core.constants import FORBIDDEN_APP_URL_TAGS


class GameConfig(AppConfig):
    def __init__(
        self,
        app_name,
        app_module,
        long_name,
        package_name,
        url_tag,
        url_namespace,
        setting_model=None,
        setting_form=None,
        answer_model=None,
        answer_model_fields=None,
        management_commands=None,
        illustration_path=None,
    ):
        super().__init__(app_name, app_module)
        self.is_game = True

        self.name = app_name
        self.long_name = long_name
        self.package_name = package_name
        if url_tag in FORBIDDEN_APP_URL_TAGS:
            raise ValueError(
                f"The game app {package_name} has url_tag `{url_tag}` which is "
                f"forbidden. Choose another url tag for the app."
            )
        self.url_tag = url_tag
        self.url_namespace = url_namespace
        self.setting_model = setting_model
        self.setting_form = setting_form
        self.answer_model = answer_model
        self.answer_model_fields = answer_model_fields
        if type(management_commands) == str:
            management_commands = [management_commands]
        elif isinstance(management_commands, Iterable):
            management_commands = list(management_commands)
        elif management_commands is not None:
            raise TypeError(
                "The management_commands parameter of a GameConfig needs to be either "
                "a string or a collection of string."
            )
        self.management_commands = management_commands
        self.illustration_path = illustration_path

    def ready(self):
        INSTALLED_GAMES.append(self)
        INSTALLED_GAMES_CHOICES.append((self.name, self.long_name))

    def register_models(self, setting_model=None, setting_form=None, answer_model=None):
        if setting_model:
            self.setting_model = setting_model
        if setting_form:
            self.setting_form = setting_form
        if answer_model:
            self.answer_model = answer_model


INSTALLED_GAMES = []
INSTALLED_GAMES_CHOICES = []
