from django.db import models

from core.models import Player, Game


class Answer(models.Model):
    game = models.ForeignKey(Game,
                             on_delete=models.CASCADE)
    player = models.ForeignKey(Player,
                               on_delete=models.CASCADE,
                               related_name='player_numberGame')
    answer = models.FloatField()
    motivation = models.TextField()
    gap = models.FloatField(null=True)
    winner = models.BooleanField(null=True,
                                 default=False)

    def formatted_answer(self):
        if int(self.answer) == self.answer:
            return int(self.answer)
        return self.answer

    class Meta:
        ordering = ['winner', 'player']
        unique_together = ('game', 'player')

    def __str__(self):
        return "[{}] {} - {} - {} {}".format(self.game.session,
                                             self.game.name,
                                             self.player.name,
                                             self.answer,
                                             "(win)" if self.winner else "")


class Result(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name='result')
    histo_js_data = models.TextField(null=True, blank=True)
    histo_bin_size = models.PositiveIntegerField()
    average = models.FloatField(null=True,
                                blank=True)
    corrected_average = models.FloatField(null=True,
                                          blank=True)

    class Meta:
        ordering = ['game']

    def __str__(self):
        return "{}".format(self.game.name)
