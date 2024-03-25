from django.db import models

from core.models import Player, Game


class Setting(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="centi_setting"
    )
    payoff_d_p1 = models.FloatField(
        default=10,
        help_text="Payoff of player 1 for the path: 'down'."
    )
    payoff_d_p2 = models.FloatField(
        default=10,
        help_text="Payoff of player 2 for the path: 'down'."
    )
    payoff_rd_p1 = models.FloatField(
        default=0,
        help_text="Payoff of player 1 for the path: 'right - down'."
    )
    payoff_rd_p2 = models.FloatField(
        default=40,
        help_text="Payoff of player 2 for the path: 'right - down'."
    )
    payoff_rrd_p1 = models.FloatField(
        default=30,
        help_text="Payoff of player 1 for the path: 'right - right - down'."
    )
    payoff_rrd_p2 = models.FloatField(
        default=30,
        help_text="Payoff of player 2 for the path: 'right - right - down'."
    )
    payoff_rrrd_p1 = models.FloatField(
        default=20,
        help_text="Payoff of player 1 for the path: 'right - right - right - down'."
    )
    payoff_rrrd_p2 = models.FloatField(
        default=60,
        help_text="Payoff of player 2 for the path: 'right - right - right - down'."
    )
    payoff_rrrr_p1 = models.FloatField(
        default=50,
        help_text="Payoff of player 1 for the path: 'right - right - right - right'."
    )
    payoff_rrrr_p2 = models.FloatField(
        default=50,
        help_text="Payoff of player 2 for the path: 'right - right - right - right'."
    )


class Answer(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="centi_answers"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="centi_answers"
    )
    strategy_as_p1 = models.CharField(max_length=100)
    strategy_as_p2 = models.CharField(max_length=100)
    avg_score_as_p1 = models.FloatField(default=0.0, null=True, blank=True)
    avg_score_as_p2 = models.FloatField(default=0.0, null=True, blank=True)
    avg_score = models.FloatField(default=0.0, null=True, blank=True)
    winning = models.BooleanField(default=False)
    motivation = models.TextField()

    class Meta:
        ordering = ["game", "player"]
        unique_together = ("game", "player")

    def __str__(self):
        return "[{}] {} - {} - ({}, {})".format(
            self.game.session,
            self.game.name,
            self.player.name,
            self.strategy_as_p1,
            self.strategy_as_p2,
        )


class Result(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="result_centi"
    )
    histo_strat1_js_data = models.TextField(null=True, blank=True)
    histo_strat2_js_data = models.TextField(null=True, blank=True)
    scores_heatmap_js_data = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["game"]

    def __str__(self):
        return "[{}] {}".format(self.game.session, self.game.name)
