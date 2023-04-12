from django.db import models

from core.models import Player, Game


class Answer(models.Model):
    game = models.ForeignKey(Game,
                             on_delete=models.CASCADE,
                             related_name='centi_answers')
    player = models.ForeignKey(Player,
                               on_delete=models.CASCADE,
                               related_name='centi_answers')
    strategy_as_p1 = models.CharField(max_length=100)
    strategy_as_p2 = models.CharField(max_length=100)
    avg_score_as_p1 = models.FloatField(default=0.0, null=True, blank=True)
    avg_score_as_p2 = models.FloatField(default=0.0, null=True, blank=True)
    avg_score = models.FloatField(default=0.0, null=True, blank=True)
    motivation = models.TextField()

    class Meta:
        ordering = ['game', 'player']
        unique_together = ('game', 'player')

    def __str__(self):
        return "[{}] {} - {}".format(self.game.session,
                                     self.game.name,
                                     self.player.name)


class Result(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name='result_centi')
    histo_strat1_js_data = models.TextField(null=True, blank=True)
    histo_strat2_js_data = models.TextField(null=True, blank=True)
    scores_heatmap_js_data = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['game']

    def __str__(self):
        return "{} - Results Data".format(self.game.name)
