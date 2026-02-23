from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from auctiongame.samplers import ALL_SAMPLERS
from core.models import Player, Game


class ArbitraryPrecisionDecimalFormField(forms.Field):
    widget = forms.TextInput

    def __init__(self, *, min_value=None, **kwargs):
        self.min_value = Decimal(str(min_value)) if min_value is not None else None

        # Remove max_length
        kwargs.pop("max_length", None)

        super().__init__(**kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Enter a valid decimal number.")

    def validate(self, value):
        super().validate(value)
        if value is not None and self.min_value is not None:
            if value < self.min_value:
                raise forms.ValidationError(
                    f"Ensure this value is greater than or equal to {self.min_value}."
                )


class ArbitraryPrecisionDecimalField(models.TextField):
    description = "Arbitrary precision decimal stored as text"

    def to_python(self, value):
        if value is None or isinstance(value, Decimal):
            return value
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError):
            raise ValidationError("Invalid decimal value.")

    def formfield(self, **kwargs):
        defaults = {
            "form_class": ArbitraryPrecisionDecimalFormField
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


class Setting(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="auction_setting"
    )
    number_auctions = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text="The number of auctions to choose from when randomly assigning a player.",
    )
    valuation_sampler = models.CharField(
        choices=zip(ALL_SAMPLERS.keys(), ALL_SAMPLERS.keys()),
        max_length=20,
        help_text="The sampling function used to assign player a valuation. 'Constant' always "
                  "return 10 + auction_id. 'Uniform' samples an integer uniformly at random "
                  "between 7 + auction_id and 13 + auction id. 'Binomial' samples an integer "
                  "from a binomial distribution with p = 0.5 and n = 2 * (10 + auction_id).",
        default="constant"
    )


class Answer(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="auct_answers"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="auct_answers"
    )
    auction_id = models.IntegerField()
    valuation = models.IntegerField()
    bid = ArbitraryPrecisionDecimalField(null=True)
    utility = ArbitraryPrecisionDecimalField(null=True)
    winning_auction = models.BooleanField(default=False)
    winning_global = models.BooleanField(default=False)
    motivation = models.TextField()
    submission_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["game", "auction_id", "player", "bid"]
        unique_together = ("game", "player")

    def __str__(self):
        return "[{}] {} - {} - {}: {}".format(
            self.game.session,
            self.game.name,
            self.player.name,
            self.auction_id,
            self.bid,
        )


class Result(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="results_auct"
    )
    auction_id = models.IntegerField()
    histo_bids_js_data = models.TextField(null=True, blank=True)
    histo_val_js_data = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["game"]
        unique_together = ("game", "auction_id")

    def __str__(self):
        return "[{}] {} - {}".format(self.game.session, self.game.name, self.auction_id)
