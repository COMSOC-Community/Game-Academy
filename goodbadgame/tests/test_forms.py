from django.test import TestCase

from core.tests.helpers import make_session
from goodbadgame.forms import SettingForm
from goodbadgame.tests.helpers import make_goodbad_game, make_question


class SettingFormTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdformsession")
        self.game = make_goodbad_game(self.session)

    def test_valid_data_is_accepted(self):
        q1 = make_question("gdbdformq1")
        q2 = make_question("gdbdformq2")
        form = SettingForm(
            data={"num_displayed_questions": "5", "questions": [q1.pk, q2.pk]}
        )
        self.assertTrue(form.is_valid())

    def test_negative_num_displayed_questions_is_rejected(self):
        form = SettingForm(data={"num_displayed_questions": "-1", "questions": []})
        self.assertFalse(form.is_valid())
        self.assertIn("num_displayed_questions", form.errors)

    def test_questions_field_is_optional(self):
        form = SettingForm(data={"num_displayed_questions": "5"})
        self.assertTrue(form.is_valid())
