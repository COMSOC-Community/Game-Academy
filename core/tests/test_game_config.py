import numbersgame

from django.test import SimpleTestCase

from core.forms import LoginForm
from core.game_config import GameConfig
from core.models import Session
from numbersgame.forms import SettingForm
from numbersgame.models import Setting, Answer


def make_game_config(**overrides):
    kwargs = dict(
        app_name="numbersgame",
        app_module=numbersgame,
        long_name="Numbers Game",
        package_name="numbersgame",
        url_tag="numbers",
        url_namespace="numbers_game",
    )
    kwargs.update(overrides)
    return GameConfig(**kwargs)


class GameConfigInitTests(SimpleTestCase):
    def test_single_management_command_string_is_normalised_to_a_list(self):
        config = make_game_config(management_commands="numbersgame_results")
        self.assertEqual(config.management_commands, ["numbersgame_results"])

    def test_management_commands_iterable_of_strings_is_kept(self):
        config = make_game_config(management_commands=["a_command", "b_command"])
        self.assertEqual(config.management_commands, ["a_command", "b_command"])

    def test_management_commands_with_non_string_item_raises(self):
        with self.assertRaises(TypeError):
            make_game_config(management_commands=["ok_command", 5])

    def test_management_commands_non_iterable_raises(self):
        with self.assertRaises(TypeError):
            make_game_config(management_commands=5)

    def test_update_management_commands_string_is_normalised_to_a_list(self):
        config = make_game_config(update_management_commands="fast_command")
        self.assertEqual(config.update_management_commands, ["fast_command"])

    def test_update_management_commands_with_non_string_item_raises(self):
        with self.assertRaises(TypeError):
            make_game_config(update_management_commands=["ok_command", 5])

    def test_illustration_paths_with_non_string_item_raises(self):
        with self.assertRaises(TypeError):
            make_game_config(illustration_paths=["numbersgame/img/NumbersGame1.png", 5])

    def test_illustration_paths_non_iterable_raises(self):
        with self.assertRaises(TypeError):
            make_game_config(illustration_paths=5)

    def test_answer_model_fields_non_iterable_raises(self):
        with self.assertRaises(TypeError):
            make_game_config(answer_model_fields=5)


class GameConfigValidateAppTests(SimpleTestCase):
    def test_fully_valid_config_does_not_raise(self):
        config = make_game_config(
            management_commands=["numbersgame_results"],
            illustration_paths=("numbersgame/img/NumbersGame1.png",),
            home_view="index",
        )
        config.register_models(setting_model=Setting, setting_form=SettingForm, answer_model=Answer)
        config.validate_app()  # should not raise

    def test_unknown_management_command_raises(self):
        config = make_game_config(management_commands=["not_a_real_command_xyz"])
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_unknown_update_management_command_raises(self):
        # Regression guard: validate_app() must check each of management_commands and
        # update_management_commands independently, not the former twice.
        config = make_game_config(
            management_commands=["numbersgame_results"],
            update_management_commands=["not_a_real_command_xyz"],
        )
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_update_management_commands_without_management_commands_warns(self):
        config = make_game_config(
            management_commands=None, update_management_commands=["numbersgame_results"],
        )
        with self.assertWarns(UserWarning):
            config.validate_app()

    def test_setting_model_not_a_model_class_raises(self):
        config = make_game_config()
        config.register_models(setting_model="not_a_model")
        with self.assertRaises(TypeError):
            config.validate_app()

    def test_setting_model_missing_game_field_raises(self):
        config = make_game_config()
        config.register_models(setting_model=Session)
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_setting_model_game_field_not_onetoone_raises(self):
        # Answer.game is a ForeignKey, not a OneToOneField.
        config = make_game_config()
        config.register_models(setting_model=Answer)
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_setting_form_not_a_modelform_raises(self):
        config = make_game_config()
        config.register_models(setting_model=Setting, setting_form=LoginForm)
        with self.assertRaises(TypeError):
            config.validate_app()

    def test_answer_model_not_a_model_class_raises(self):
        config = make_game_config()
        config.register_models(answer_model="not_a_model")
        with self.assertRaises(TypeError):
            config.validate_app()

    def test_answer_model_missing_game_field_raises(self):
        config = make_game_config()
        config.register_models(answer_model=Session)
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_answer_model_fields_with_unknown_field_raises(self):
        config = make_game_config(answer_model_fields=("not_a_real_field",))
        config.register_models(answer_model=Answer)
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_answer_model_fields_valid_fields_do_not_raise(self):
        config = make_game_config(answer_model_fields=("answer", "motivation"))
        config.register_models(answer_model=Answer)
        config.validate_app()  # should not raise

    def test_answer_model_fields_without_answer_model_raises(self):
        config = make_game_config(answer_model_fields=("answer",))
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_home_view_that_does_not_exist_raises(self):
        config = make_game_config(home_view="not_a_real_view_name")
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_home_view_that_exists_does_not_raise(self):
        config = make_game_config(home_view="submit_answer")
        config.validate_app()  # should not raise

    def test_illustration_path_not_a_static_file_raises(self):
        config = make_game_config(illustration_paths=("not/a/real/static/path.png",))
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_answer_to_csv_func_not_callable_raises(self):
        config = make_game_config(answer_to_csv_func="not_callable")
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_settings_to_csv_func_not_callable_raises(self):
        config = make_game_config(settings_to_csv_func="not_callable")
        with self.assertRaises(ValueError):
            config.validate_app()

    def test_random_answers_func_not_callable_raises(self):
        config = make_game_config(random_answers_func="not_callable")
        with self.assertRaises(ValueError):
            config.validate_app()
