from django.db import models

from core.models import Team, Game


class Answer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='itepris_answers')
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='itepris_answer')
    automata = models.TextField()
    motivation = models.TextField()
    name = models.CharField(max_length=100, unique=True)
    score = models.FloatField(default=0.0, blank=True, null=True)
    winner = models.BooleanField(blank=True, null=True)

    class Meta:
        ordering = ['game', 'winner', 'team']
        unique_together = ('game', 'team')

    def __str__(self):
        return "[{}] {} - {} - {} {}".format(self.game.session,
                                             self.game.name,
                                             self.team.name,
                                             self.score,
                                             "(win)" if self.winner else "")
