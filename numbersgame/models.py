from django.db import models

from core.models import Player, Game


class Setting(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="numbers_setting"
    )
    factor = models.FloatField(
        default=2/3,
        help_text="The winning number is the closest one to the average submitted number times the "
        "factor.",
    )
    factor_display = models.CharField(
        default="2/3",
        help_text="The strict used to display the multiplicative factor (useful when there are "
        "infinitely many digits).",
        max_length=30,
    )
    histogram_bin_size = models.FloatField(
        default=3,
        help_text="The size of the bins used in the histogram presenting the answers.",
    )


class Answer(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="numbers_answers"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="numbers_answer"
    )
    answer = models.FloatField()
    motivation = models.TextField()
    gap = models.FloatField(null=True)
    winner = models.BooleanField(null=True, default=False)

    def formatted_answer(self):
        if int(self.answer) == self.answer:
            return int(self.answer)
        return self.answer

    class Meta:
        ordering = ["game", "winner", "player"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "player"], name="ng_game_player_unique"
            )
        ]

    def __str__(self):
        return "[{}] {} - {} - {} {}".format(
            self.game.session,
            self.game.name,
            self.player.name,
            self.answer,
            "(win)" if self.winner else "",
        )


class Result(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="result_ng"
    )
    histo_js_data = models.TextField(null=True, blank=True)
    average = models.FloatField(null=True, blank=True)
    corrected_average = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["game"]

    def __str__(self):
        return "{} - Results Data".format(self.game.name)
