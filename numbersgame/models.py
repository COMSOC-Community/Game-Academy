from django.db import models

from core.models import Player, Game


class Answer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player_numberGame')
    answer = models.FloatField()
    motivation = models.TextField()

    def formatted_answer(self):
        if int(self.answer) == self.answer:
            return int(self.answer)
        return self.answer

    class Meta:
        ordering = ['player']
        unique_together = ('game', 'player')

    def __str__(self):
        return "[{}] {} - {}".format(self.game.session, self.game.name, self.player.name)
