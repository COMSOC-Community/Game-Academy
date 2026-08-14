from types import SimpleNamespace

from django.test import SimpleTestCase

from core.templatetags.core_extras import (
    get_key_dict,
    get_key_dict_default,
    get_attr,
    float_formatter,
    percentage,
    subtract,
    absolute,
)


class GetKeyDictTests(SimpleTestCase):
    def test_returns_value_for_existing_key(self):
        self.assertEqual(get_key_dict({"a": 1}, "a"), 1)

    def test_raises_for_missing_key(self):
        with self.assertRaises(KeyError):
            get_key_dict({"a": 1}, "b")


class GetKeyDictDefaultTests(SimpleTestCase):
    def test_returns_value_for_existing_key(self):
        self.assertEqual(get_key_dict_default({"a": 1}, "a"), 1)

    def test_returns_none_for_missing_key(self):
        self.assertIsNone(get_key_dict_default({"a": 1}, "b"))


class GetAttrTests(SimpleTestCase):
    def test_returns_attribute_value(self):
        obj = SimpleNamespace(name="mysession")
        self.assertEqual(get_attr(obj, "name"), "mysession")

    def test_coerces_non_string_attr_name(self):
        obj = SimpleNamespace()
        setattr(obj, "123", "value")
        self.assertEqual(get_attr(obj, 123), "value")

    def test_raises_for_missing_attribute(self):
        obj = SimpleNamespace(name="mysession")
        with self.assertRaises(AttributeError):
            get_attr(obj, "does_not_exist")


class FloatFormatterFilterTests(SimpleTestCase):
    def test_formats_numeric_value(self):
        self.assertEqual(float_formatter(3.14159), "3.142")

    def test_non_numeric_value_returns_empty_string(self):
        self.assertEqual(float_formatter("not a number"), "")

    def test_none_returns_empty_string(self):
        self.assertEqual(float_formatter(None), "")

    def test_respects_num_digits(self):
        self.assertEqual(float_formatter(3.14159, num_digits=1), "3.1")


class PercentageFilterTests(SimpleTestCase):
    def test_converts_fraction_to_percentage(self):
        self.assertEqual(percentage(0.5), "50")

    def test_non_numeric_value_returns_empty_string(self):
        self.assertEqual(percentage("nope"), "")

    def test_respects_num_digits(self):
        self.assertEqual(percentage(0.3333, num_digits=1), "33.3")


class SubtractFilterTests(SimpleTestCase):
    def test_subtracts_arg_from_value(self):
        self.assertEqual(subtract(10, 3), 7)

    def test_works_with_floats(self):
        self.assertAlmostEqual(subtract(1.5, 0.5), 1.0)


class AbsoluteFilterTests(SimpleTestCase):
    def test_negative_value(self):
        self.assertEqual(absolute(-5), 5)

    def test_positive_value_unchanged(self):
        self.assertEqual(absolute(5), 5)
