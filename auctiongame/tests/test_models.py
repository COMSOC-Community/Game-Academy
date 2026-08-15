from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.test import TestCase, SimpleTestCase

from core.tests.helpers import make_session, make_user, make_player
from auctiongame.models import (
    Answer,
    ArbitraryPrecisionDecimalField,
    ArbitraryPrecisionDecimalFormField,
    Result,
    Setting,
)
from auctiongame.tests.helpers import make_auction_game


class ArbitraryPrecisionDecimalFieldTests(SimpleTestCase):
    def setUp(self):
        self.field = ArbitraryPrecisionDecimalField()

    def test_to_python_none_stays_none(self):
        self.assertIsNone(self.field.to_python(None))

    def test_to_python_decimal_passthrough(self):
        value = Decimal("1.5")
        self.assertIs(self.field.to_python(value), value)

    def test_to_python_parses_string(self):
        self.assertEqual(self.field.to_python("3.14159265358979"), Decimal("3.14159265358979"))

    def test_to_python_raises_on_invalid_string(self):
        with self.assertRaises(DjangoValidationError):
            self.field.to_python("not-a-decimal")

    def test_from_db_value_parses_raw_stored_string(self):
        self.assertEqual(
            self.field.from_db_value("5.123456789012345", None, None),
            Decimal("5.123456789012345"),
        )

    def test_from_db_value_none_stays_none(self):
        self.assertIsNone(self.field.from_db_value(None, None, None))

    def test_formfield_uses_custom_form_field_class(self):
        formfield = self.field.formfield()
        self.assertIsInstance(formfield, ArbitraryPrecisionDecimalFormField)


class ArbitraryPrecisionDecimalFormFieldTests(SimpleTestCase):
    def test_to_python_empty_value_is_none(self):
        field = ArbitraryPrecisionDecimalFormField(required=False)
        self.assertIsNone(field.to_python(""))

    def test_to_python_parses_valid_decimal(self):
        field = ArbitraryPrecisionDecimalFormField(required=False)
        self.assertEqual(field.to_python("2.71828182845905"), Decimal("2.71828182845905"))

    def test_to_python_raises_on_invalid_value(self):
        from django import forms

        field = ArbitraryPrecisionDecimalFormField(required=False)
        with self.assertRaises(forms.ValidationError):
            field.to_python("not-a-decimal")

    def test_validate_rejects_below_min_value(self):
        from django import forms

        field = ArbitraryPrecisionDecimalFormField(required=False, min_value=0)
        with self.assertRaises(forms.ValidationError):
            field.validate(Decimal("-0.01"))

    def test_validate_accepts_min_value_itself(self):
        field = ArbitraryPrecisionDecimalFormField(required=False, min_value=0)
        field.validate(Decimal("0"))


class SettingModelTests(TestCase):
    def setUp(self):
        self.session = make_session("auctsettingsession")
        self.game = make_auction_game(self.session)

    def test_default_values(self):
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(setting.number_auctions, 5)
        self.assertEqual(setting.valuation_sampler, "constant")

    def test_number_auctions_below_one_fails_validation(self):
        setting = Setting(game=self.game, number_auctions=0)
        with self.assertRaises(DjangoValidationError):
            setting.full_clean()

    def test_one_to_one_with_game(self):
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(self.game.auction_setting, setting)


class AnswerModelTests(TestCase):
    def setUp(self):
        self.session = make_session("auctanswersession")
        self.game = make_auction_game(self.session)
        self.user = make_user("auctanswerplayer")
        self.player = make_player(self.session, self.user)

    def test_str(self):
        answer = Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10,
            bid=Decimal("5.5"), motivation="m",
        )
        self.assertIn(self.player.name, str(answer))
        self.assertIn("5.5", str(answer))

    def test_bid_round_trips_through_the_database_as_decimal(self):
        answer = Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10,
            bid=Decimal("5.123456789012345"), motivation="m",
        )
        answer.refresh_from_db()
        self.assertEqual(answer.bid, Decimal("5.123456789012345"))
        self.assertIsInstance(answer.bid, Decimal)

    def test_unique_together_game_player(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10, motivation="m"
        )
        with self.assertRaises(IntegrityError):
            Answer.objects.create(
                game=self.game, player=self.player, auction_id=2, valuation=11, motivation="m2"
            )


class ResultModelTests(TestCase):
    def setUp(self):
        self.session = make_session("auctresultsession")
        self.game = make_auction_game(self.session)

    def test_str(self):
        result = Result.objects.create(game=self.game, auction_id=1)
        self.assertIn("1", str(result))

    def test_unique_together_game_auction_id(self):
        Result.objects.create(game=self.game, auction_id=1)
        with self.assertRaises(IntegrityError):
            Result.objects.create(game=self.game, auction_id=1)

    def test_same_auction_id_allowed_for_different_games(self):
        other_game = make_auction_game(self.session, url_tag="auct2", name="Auction2")
        Result.objects.create(game=self.game, auction_id=1)
        # Should not raise.
        Result.objects.create(game=other_game, auction_id=1)
