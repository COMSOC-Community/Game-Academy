import importlib
import warnings
from collections.abc import Iterable

from django.apps import AppConfig
from django.contrib.staticfiles import finders
from django.core.management import get_commands
from django.db.models import Model
from django.db.models.base import ModelBase
from django.forms import Form, BaseForm
from django.forms.models import ModelFormMetaclass

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
        *,
        setting_model=None,
        setting_form=None,
        answer_model=None,
        answer_model_fields=None,
        home_view=None,
        management_commands=None,
        update_management_commands=None,
        illustration_paths=None,
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

        if isinstance(answer_model_fields, Iterable):
            if not all(isinstance(c, str) for c in answer_model_fields):
                raise TypeError(
                    "The answer_model_fields parameter of a GameConfig needs to be a collection of "
                    "string."
                )
        elif answer_model_fields is not None:
            raise TypeError(
                    "The answer_model_fields parameter of a GameConfig needs to be a collection of "
                    "string."
            )
        self.answer_model_fields = answer_model_fields

        if home_view is not None and not isinstance(home_view, str):
            raise TypeError("The home_view parameter of a GameConfig needs to be a string.")
        self.home_view = home_view

        # Management commands
        if isinstance(management_commands, str):
            management_commands = [management_commands]
        elif isinstance(management_commands, Iterable):
            if not all(isinstance(c, str) for c in management_commands):
                raise TypeError(
                    "If iterable, the management_commands parameter of a GameConfig needs to be "
                    "a collection of string."
                )
            management_commands = list(management_commands)
        elif management_commands is not None:
            raise TypeError(
                "The management_commands parameter of a GameConfig needs to be either "
                "a string or a collection of string."
            )
        self.management_commands = management_commands
        if isinstance(update_management_commands, str):
            update_management_commands = [update_management_commands]
        elif isinstance(update_management_commands, Iterable):
            if not all(isinstance(c, str) for c in update_management_commands):
                raise TypeError(
                    "If iterable, the update_management_commands parameter of a GameConfig needs "
                    "to be a collection of string."
                )
            update_management_commands = list(update_management_commands)
        elif update_management_commands is not None:
            raise TypeError(
                "The update_management_commands parameter of a GameConfig needs to be either "
                "a string or a collection of string."
            )
        self.update_management_commands = update_management_commands

        # Illustration Paths
        if isinstance(illustration_paths, Iterable):
            if not all(isinstance(c, str) for c in illustration_paths):
                raise TypeError(
                    "The illustration_paths parameter of a GameConfig needs to be a collection of "
                    "string."
                )
        elif illustration_paths is not None:
            raise TypeError(
                    "The illustration_paths parameter of a GameConfig needs to be a collection of "
                    "string."
            )
        self.illustration_paths = illustration_paths

    def ready(self):
        INSTALLED_GAMES.append(self)
        INSTALLED_GAMES_CHOICES.append((self.name, self.long_name))
        self.validate_app()

    def register_models(self, setting_model=None, setting_form=None, answer_model=None):
        if setting_model:
            self.setting_model = setting_model
        if setting_form:
            self.setting_form = setting_form
        if answer_model:
            self.answer_model = answer_model

    def validate_app(self):
        # Check that management commands exist
        if self.management_commands is not None or self.update_management_commands is not None:
            all_commands = {c[0] for c in get_commands().items() if c[1] == self.name}
            for commands in [self.management_commands, self.update_management_commands]:
                if commands is not None:
                    for c in self.management_commands:
                        if c not in all_commands:
                            raise ValueError(f"For the app {self.name}, the management command "
                                             f"{c} does not seem to exist.")
            if self.update_management_commands is not None and self.management_commands is None:
                warnings.warn(f"WARNING: For the app {self.name}, you have update management "
                              f"commands but no management commands. This is counter-intuitive "
                              f"(but shall not lead to errors).")

        # Check that the illustration paths corresponds to static files
        if self.illustration_paths is not None:
            for illustration_path in self.illustration_paths:
                found = finders.find(illustration_path)
                if found is None:
                    raise ValueError(f"For the app {self.name}, the illustration path "
                                     f"{illustration_path} cannot be found in the static folder.")

        # Check that the models and forms are indeed models and forms
        if self.setting_model is not None and not isinstance(self.setting_model, ModelBase):
            raise TypeError("The setting_model attribute of a GameConfig needs to be a "
                            "Django Model object.")
        if self.setting_form is not None and not isinstance(self.setting_form, ModelFormMetaclass):
            raise TypeError("The setting_form attribute of a GameConfig needs to be a "
                            "Django Form object.")
        if self.answer_model is not None and not isinstance(self.answer_model, ModelBase):
            print(self.answer_model)
            print(type(self.answer_model))
            raise TypeError("The answer_model attribute of a GameConfig needs to be a "
                            "Django Model object.")
        if self.answer_model_fields is not None:
            if self.answer_model is None:
                raise ValueError("You have specified an field for the answer model but not the "
                                 "answer model itself.")
            for field in self.answer_model_fields:
                if not hasattr(self.answer_model, field):
                    raise ValueError(f"The answer model you provided does not seem to have "
                                     f"{field} as a field.")

        # Check that home view is a view
        if self.home_view is not None:
            urls = getattr(importlib.import_module(f'{self.name}.urls'), "urlpatterns")
            if self.home_view not in set(url.name for url in urls):
                raise ValueError(f"The home_view value {self.home_view} does not seem to be a view "
                                 f"for the app {self.name}")


INSTALLED_GAMES = []
INSTALLED_GAMES_CHOICES = []
