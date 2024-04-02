from django.db import models

from core.models import Player, Game


class Setting(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="simp_poker_setting"
    )


#     setting1 = models.FloatField()


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


# class Result(models.Model):
#     game = models.OneToOneField(
#         Game, on_delete=models.CASCADE, related_name="simp_poker_results"
#     )
#     result = models.FloatField()
