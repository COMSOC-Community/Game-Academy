from django.db import models

from core.models import Player, Game


class Setting(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="itepris_setting"
    )
    num_repetitions = models.CharField(
        default="168, 359, 306, 622, 319",
        help_text="The number of rounds each strategy play against every other strategies. "
                  "Several number of rounds can be indicated by using a comma-separated list.",
        max_length=50,
    )
    store_scores = models.BooleanField(
        default=True,
        help_text="If selected, the non-aggregated scores are stored (for every pair of answer "
                  "and every round). For large number of answers there will be many such scores, "
                  "it can then be good to de-activate this."
    )
    payoff_high = models.FloatField(
        default=0,
        help_text="Payoff of the defecting player when one player defects and the other cooperates.",
    )
    payoff_medium = models.FloatField(
        default=-10, help_text="Payoff of both players when they both cooperate."
    )
    payoff_low = models.FloatField(
        default=-20, help_text="Payoff of both players when they both defect."
    )
    payoff_tiny = models.FloatField(
        default=-25,
        help_text="Payoff of the cooperating player when one player defects and the other "
        "cooperates.",
    )
    forbidden_strategies = models.TextField(
        blank=True,
        null=True,
        help_text="Specify here a list of forbidden strategies. Specify the strategies by using "
        "the same syntax as the one used to submit an answer. Separate strategies by "
        "a line starting with '---'. Forbidden strategies (and isomorphic ones) cannot "
        "be submitted.",
    )


class Answer(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="itepris_answers"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="itepris_answer"
    )
    automata = models.TextField()
    initial_state = models.CharField(max_length=50)
    motivation = models.TextField()
    name = models.CharField(max_length=100)
    avg_score = models.FloatField(default=0.0, blank=True, null=True)
    winner = models.BooleanField(blank=True, null=True, default=False)
    graph_json_data = models.TextField(blank=True, null=True)
    submission_time = models.DateTimeField(auto_now=True)

    def formatted_avg_score(self):
        if int(self.avg_score) == self.avg_score:
            return int(self.avg_score)
        return self.avg_score

    def number_states(self):
        return len(self.automata.split("\n"))

    class Meta:
        ordering = ["game", "winner", "player"]
        unique_together = ("game", "player")

    def __str__(self):
        return "[{}] {} - {} - {} {}".format(
            self.game.session,
            self.game.name,
            self.player.name,
            self.avg_score,
            "(win)" if self.winner else "",
        )


class Score(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="scores")
    opponent = models.ForeignKey(
        Answer, on_delete=models.CASCADE, related_name="scores_as_opp"
    )
    number_round = models.IntegerField()
    answer_avg_score = models.FloatField()
    opp_avg_score = models.FloatField()

    class Meta:
        ordering = ["answer", "opponent", "number_round"]
        unique_together = ("answer", "opponent", "number_round")

    def __str__(self):
        return "[{}] {} - {} --[{}]--> {} ({})".format(
            self.answer.game.session,
            self.answer.game.name,
            self.answer.player.name,
            self.number_round,
            self.opponent.player.name,
            self.answer_avg_score,
        )
