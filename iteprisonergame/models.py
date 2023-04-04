from django.db import models

from core.models import Team, Game


class Answer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='itepris_answers')
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='itepris_answer')
    automata = models.TextField()
    initial_state = models.CharField(max_length=50)
    motivation = models.TextField()
    name = models.CharField(max_length=100, unique=True)
    total_score = models.FloatField(default=0.0, blank=True, null=True)
    winner = models.BooleanField(blank=True, null=True)
    graph_json_data = models.TextField(blank=True, null=True)

    def formatted_total_score(self):
        if int(self.total_score) == self.total_score:
            return int(self.total_score)
        return self.total_score

    class Meta:
        ordering = ['game', 'winner', 'team']
        unique_together = ('game', 'team')

    def __str__(self):
        return "[{}] {} - {} - {} {}".format(self.game.session,
                                             self.game.name,
                                             self.team.name,
                                             self.total_score,
                                             "(win)" if self.winner else "")


class Score(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='scores')
    opponent = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='against_scores')
    number_round = models.IntegerField()
    score = models.FloatField()

    class Meta:
        ordering = ['answer', 'opponent']
        unique_together = ('answer', 'opponent', 'number_round')

    def __str__(self):
        return "[{}] {} - {} --[{}]--> {} ({})".format(self.answer.game.session,
                                                       self.answer.game.name,
                                                       self.answer.team.name,
                                                       self.number_round,
                                                       self.opponent.team.name,
                                                       self.score)
