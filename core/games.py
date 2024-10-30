import importlib
import warnings
from collections.abc import Iterable, Callable

from django.apps import AppConfig
from django.contrib.staticfiles import finders
from django.core.management import get_commands
from django.db.models.base import ModelBase
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.forms.models import ModelFormMetaclass

from core.constants import FORBIDDEN_APP_URL_TAGS


class GameConfig(AppConfig):
    """AppConfig for games. Used to ensure proper registration of everything and all."""
    def __init__(
        self,
        app_name,
        app_module,
        long_name,
        package_name,
        url_tag,
        url_namespace,
        *,
        answer_model_fields=None,
        answer_to_csv_func=None,
        random_answers_func=None,
        settings_to_csv_func=None,
        home_view=None,
        management_commands=None,
        update_management_commands=None,
        illustration_paths=None,
    ):
        super().__init__(app_name, app_module)
        self.is_game = True

        # The name of the game, typically a slug
        self.name = app_name
        # The long name of the game, includes whitespace and all
        self.long_name = long_name
        # The name of the Python module in which the game is implemented
        self.package_name = package_name
        # Ensures the url_tag is not forbidden
        if url_tag in FORBIDDEN_APP_URL_TAGS:
            raise ValueError(
                f"The game app {package_name} has url_tag `{url_tag}` which is "
                f"forbidden. Choose another url tag for the app."
            )
        self.url_tag = url_tag
        # URL namespace used by Django
        self.url_namespace = url_namespace

        # Models and Forms used by the game. Should be set with the register_models
        # method because they would not have been registered yet
        # The model used to describe the extra settings of the game
        self.setting_model = None
        # The form used to update the extra settings of the game
        self.setting_form = None
        # The model used to store the answers to the game
        self.answer_model = None

        # Field of the answer model that are displayed
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
        # Function creating a CSV file from the answers
        self.answer_to_csv_func = answer_to_csv_func
        # Function generating random answers
        self.random_answers_func = random_answers_func
        # Function creating a CSV file from the game settings
        self.settings_to_csv_func = settings_to_csv_func

        # "home" view of the game
        if home_view is not None and not isinstance(home_view, str):
            raise TypeError(
                "The home_view parameter of a GameConfig needs to be a string."
            )
        self.home_view = home_view

        # The management commands for the game. The one passed here can be run by an admin from
        # the website. Only use result rendering commands.
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
        # Commands to use when updating after every new answer. Can be different from
        # self.management_commands in case there are faster implementation to update.
        self.update_management_commands = update_management_commands

        # Paths to the illustrations of the game.
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
        """Registers the game in the system. If you override this method, always call the super."""
        INSTALLED_GAMES.append(self)
        INSTALLED_GAMES_CHOICES.append((self.name, self.long_name))
        self.validate_app()

    def register_models(self, setting_model=None, setting_form=None, answer_model=None):
        """Register models. Typically used in the overridden "ready" method to register models
        and forms that had not yet been registered within Django."""
        if setting_model:
            self.setting_model = setting_model
        if setting_form:
            self.setting_form = setting_form
        if answer_model:
            self.answer_model = answer_model

    def validate_app(self):
        """Runs checks that the app has all the necessary elements."""
        # Check that management commands exist
        if (
            self.management_commands is not None
            or self.update_management_commands is not None
        ):
            all_commands = {c[0] for c in get_commands().items() if c[1] == self.name}
            for commands in [self.management_commands, self.update_management_commands]:
                if commands is not None:
                    for c in self.management_commands:
                        if c not in all_commands:
                            raise ValueError(
                                f"For the app {self.name}, the management command "
                                f"{c} does not seem to exist."
                            )
            if (
                self.update_management_commands is not None
                and self.management_commands is None
            ):
                warnings.warn(
                    f"WARNING: For the app {self.name}, you have update management "
                    f"commands but no management commands. This is counter-intuitive "
                    f"(but shall not lead to errors)."
                )

        # Check that the illustration paths corresponds to static files
        if self.illustration_paths is not None:
            for illustration_path in self.illustration_paths:
                found = finders.find(illustration_path)
                if found is None:
                    raise ValueError(
                        f"For the app {self.name}, the illustration path "
                        f"{illustration_path} cannot be found in the static folder."
                    )

        # Check that the models and forms are indeed models and forms
        if self.setting_model is not None and not isinstance(
            self.setting_model, ModelBase
        ):
            raise TypeError(
                "The setting_model attribute of a GameConfig needs to be a "
                "Django Model object."
            )
        if self.setting_form is not None and not isinstance(
            self.setting_form, ModelFormMetaclass
        ):
            raise TypeError(
                "The setting_form attribute of a GameConfig needs to be a "
                "Django Form object."
            )
        if self.answer_model is not None:
            if not isinstance(self.answer_model, ModelBase):
                raise TypeError(
                    "The answer_model attribute of a GameConfig needs to be a "
                    "Django Model object."
                )
            if not hasattr(self.answer_model, "game"):
                raise ValueError(
                    "The answer_model attribute of a GameConfig needs to have a "
                    "'game' attribute that is a ForeignKey to a Game object."
                )
            if not isinstance(
                getattr(self.answer_model, "game"), ForwardManyToOneDescriptor
            ):
                raise ValueError(
                    "The answer_model attribute of a GameConfig needs to have a "
                    "'game' attribute that is a ForeignKey to a Game object."
                )
        if self.answer_model_fields is not None:
            if self.answer_model is None:
                raise ValueError(
                    "You have specified an field for the answer model but not the "
                    "answer model itself."
                )
            for field in self.answer_model_fields:
                if not hasattr(self.answer_model, field):
                    raise ValueError(
                        f"The answer model you provided does not seem to have "
                        f"{field} as a field."
                    )

        # Check that home view is a view
        if self.home_view is not None:
            urls = getattr(importlib.import_module(f"{self.name}.urls"), "urlpatterns")
            if self.home_view not in set(url.name for url in urls):
                raise ValueError(
                    f"The home_view value {self.home_view} does not seem to be a view "
                    f"for the app {self.name}"
                )

        # Check that the export functions are callable
        if self.answer_to_csv_func is not None:
            if not isinstance(self.answer_to_csv_func, Callable):
                raise ValueError(
                    f"The export answer function for the app {self.name} is not callable."
                )
        if self.settings_to_csv_func is not None:
            if not isinstance(self.settings_to_csv_func, Callable):
                raise ValueError(
                    f"The export settings function for the app {self.name} is not callable."
                )

        # Check that random generators are callable
        if self.random_answers_func is not None:
            if not isinstance(self.random_answers_func, Callable):
                raise ValueError(
                    f"The random answers generator for the app {self.name} is not callable."
                )


INSTALLED_GAMES = []
INSTALLED_GAMES_CHOICES = []
