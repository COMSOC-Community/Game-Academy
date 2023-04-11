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
    score = models.FloatField(default=0.0, null=True, blank=True)
    motivation = models.TextField()

    class Meta:
        ordering = ['game', 'player']
        unique_together = ('game', 'player')

    def __str__(self):
        return "[{}] {} - {}".format(self.game.session,
                                     self.game.name,
                                     self.player.name)
