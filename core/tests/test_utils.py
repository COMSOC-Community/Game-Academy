from django.test import SimpleTestCase

from core.utils import float_formatter, sanitise_filename


class FloatFormatterTests(SimpleTestCase):
    def test_default_num_digits_is_three(self):
        self.assertEqual(float_formatter(3.14159), "3.142")

    def test_trailing_zeros_are_stripped(self):
        self.assertEqual(float_formatter(3.0), "3")
        self.assertEqual(float_formatter(3.10), "3.1")

    def test_whole_number_with_zero_digits_is_not_mangled(self):
        # Regression guard: without the "." in formatted_value check, rstrip("0") would
        # incorrectly eat the trailing zeros of a whole number like "1000" -> "1".
        self.assertEqual(float_formatter(1000, num_digits=0), "1000")
        self.assertEqual(float_formatter(100, num_digits=0), "100")

    def test_negative_value(self):
        self.assertEqual(float_formatter(-2.5, num_digits=1), "-2.5")

    def test_middle_zeros_are_preserved(self):
        self.assertEqual(float_formatter(100.5, num_digits=2), "100.5")

    def test_accepts_string_input(self):
        self.assertEqual(float_formatter("5.500"), "5.5")

    def test_num_digits_none_uses_str_conversion(self):
        self.assertEqual(float_formatter(3.14159, num_digits=None), "3.14159")
        self.assertEqual(float_formatter(3.0, num_digits=None), "3")

    def test_zero(self):
        self.assertEqual(float_formatter(0), "0")


class SanitiseFilenameTests(SimpleTestCase):
    def test_strips_spaces_and_punctuation(self):
        self.assertEqual(sanitise_filename("My Session!"), "MySession")

    def test_keeps_letters_digits_and_underscore(self):
        self.assertEqual(sanitise_filename("2023_Course-Edition"), "2023_CourseEdition")

    def test_empty_string(self):
        self.assertEqual(sanitise_filename(""), "")

    def test_only_punctuation_yields_empty_string(self):
        self.assertEqual(sanitise_filename("!@#$%^&*()"), "")

    def test_unicode_word_characters_are_kept(self):
        self.assertEqual(sanitise_filename("café"), "café")
