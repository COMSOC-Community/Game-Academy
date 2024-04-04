from django.db import models

from core.models import Player, Game
from core.utils import float_formatter


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
    round_robin_position = models.IntegerField(null=True, blank=True)
    round_robin_with_opt_score = models.FloatField(null=True, blank=True, default=0)
    round_robin_with_opt_position = models.IntegerField(null=True, blank=True)
    score_against_optimum = models.FloatField(null=True, blank=True, default=0)
    winner_against_optimum = models.BooleanField(null=True, default=False)
    best_response = models.CharField(max_length=100, null=True, blank=True, default='')
    score_against_best_response = models.FloatField(null=True, blank=True, default=0)

    @property
    def probabilities_as_tuple(self):
        return f"{float_formatter(self.prob_p1_king, num_digits=5)}, " \
               f"{float_formatter(self.prob_p1_queen, num_digits=5)}, " \
               f"{float_formatter(self.prob_p1_jack, num_digits=5)}, " \
               f"{float_formatter(self.prob_p2_king, num_digits=5)}, " \
               f"{float_formatter(self.prob_p2_queen, num_digits=5)}, " \
               f"{float_formatter(self.prob_p2_jack, num_digits=5)}"

    @property
    def best_response_as_answer(self):
        split_best_response = self.best_response.split(',')
        return Answer(
            game=self.game,
            player=self.player,
            prob_p1_king=float(split_best_response[0]),
            prob_p1_queen=float(split_best_response[1]),
            prob_p1_jack=float(split_best_response[2]),
            prob_p2_king=float(split_best_response[3]),
            prob_p2_queen=float(split_best_response[4]),
            prob_p2_jack=float(split_best_response[5]),
        )

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
    optimal_strategy_round_robin_score = models.FloatField(null=True, blank=True, default=0)
    optimal_strategy_round_robin_position = models.IntegerField(null=True, blank=True)
    global_best_response = models.CharField(max_length=100, null=True, blank=True)
    global_best_response_rr_score = models.FloatField(null=True, blank=True, default=0)

    def global_best_response_as_answer(self):
        split_best_response = self.global_best_response.split(',')
        return Answer(
            game=self.game,
            player=self.game.session.players.first(),
            prob_p1_king=float(split_best_response[0]),
            prob_p1_queen=float(split_best_response[1]),
            prob_p1_jack=float(split_best_response[2]),
            prob_p2_king=float(split_best_response[3]),
            prob_p2_queen=float(split_best_response[4]),
            prob_p2_jack=float(split_best_response[5]),
        )

    class Meta:
        ordering = ["game"]

    def __str__(self):
        return "{} - Results Data".format(self.game.name)
