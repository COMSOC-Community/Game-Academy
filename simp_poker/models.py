from django.db import models

from core.models import Player, Game


class Setting(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="simp_poker_setting"
    )


class Answer(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="simp_poker_answers"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="simp_poker_answer"
    )
    prob_p1_king = models.FloatField()
    prob_p1_queen = models.FloatField()
    prob_p1_jack = models.FloatField()
    prob_p2_king = models.FloatField()
    prob_p2_queen = models.FloatField()
    prob_p2_jack = models.FloatField()
    motivation = models.TextField()
    round_robin_score = models.FloatField(null=True, blank=True, default=0)
    round_robin_with_opt_score = models.FloatField(null=True, blank=True, default=0)
    round_robin_winner = models.BooleanField(null=True, default=False)
    score_against_optimum = models.FloatField(null=True, blank=True, default=0)
    winner_against_optimum = models.BooleanField(null=True, default=False)
    best_response = models.CharField(max_length=100, null=True, blank=True, default='')
    score_against_best_response = models.FloatField(null=True, blank=True, default=0)

    class Meta:
        ordering = ["game", "player", "round_robin_score"]
        unique_together = ("game", "player")

    def __str__(self):
        return "[{}] {} - {}".format(
            self.game.session,
            self.game.name,
            self.player.name,
        )


class Result(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="simp_poker_res"
    )
    optimal_strategy_score = models.FloatField(null=True, blank=True, default=0)

    class Meta:
        ordering = ["game"]

    def __str__(self):
        return "{} - Results Data".format(self.game.name)
