from django.db import models

from core.models import Player, Game


class Answer(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="auct_answers"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="auct_answers"
    )
    auction_id = models.IntegerField()
    bid = models.FloatField(null=True)
    utility = models.FloatField(null=True)
    winning_auction = models.BooleanField(default=False)
    winning_global = models.BooleanField(default=False)
    motivation = models.TextField()
    submission_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["game", "player"]
        unique_together = ("game", "player")

    def __str__(self):
        return "[{}] {} - {} - {}: {}".format(
            self.game.session,
            self.game.name,
            self.player.name,
            self.auction_id,
            self.bid,
        )


class Result(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="result_auct"
    )
    histo_auct1_js_data = models.TextField(null=True, blank=True)
    histo_auct2_js_data = models.TextField(null=True, blank=True)
    histo_auct3_js_data = models.TextField(null=True, blank=True)
    histo_auct4_js_data = models.TextField(null=True, blank=True)
    histo_auct5_js_data = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["game"]

    def __str__(self):
        return "[{}] {}".format(self.game.session, self.game.name)
