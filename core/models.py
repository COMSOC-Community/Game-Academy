from django.db import models
from django.contrib.auth.models import Group, AbstractUser

from gameserver.games import INSTALLED_GAMES_SETTING


class CustomUser(AbstractUser):
    is_player = models.BooleanField(blank=True, null=True, default=False)
    is_guest_player = models.BooleanField(blank=True, null=True, default=False)

    def display_name(self):
        if self.is_player:
            return self.players.first().name
        return self.username

    def __str__(self):
        return self.username


class Session(models.Model):
    url_tag = models.SlugField(unique=True, max_length=50, blank=False, null=False)
    name = models.CharField(unique=True, max_length=50, blank=False, null=False)
    long_name = models.CharField(max_length=100, blank=False, null=False)
    can_register = models.BooleanField(default=True)
    need_registration = models.BooleanField(default=True)
    visible = models.BooleanField(default=False)
    admins = models.ManyToManyField(CustomUser, related_name="administrated_sessions")
    super_admins = models.ManyToManyField(CustomUser, related_name="super_administrated_sessions")

    class Meta:
        ordering = ["url_tag"]

    def __str__(self):
        return str(self.url_tag)


class Player(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="players"
    )
    name = models.SlugField(max_length=100, blank=False, null=False)
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, blank=False, null=False, related_name="players"
    )
    is_guest = models.BooleanField(default=False)

    class Meta:
        ordering = ["session", "name"]
        unique_together = ("name", "session")

    def __str__(self):
        return "[{}] {}".format(self.session, self.name)


class Game(models.Model):
    game_type = models.CharField(max_length=100, blank=False, null=False)
    name = models.CharField(max_length=100, blank=False, null=False)
    url_tag = models.SlugField(max_length=10, blank=False, null=False)
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, blank=False, null=False
    )
    playable = models.BooleanField(default=True)
    visible = models.BooleanField(default=False)
    results_visible = models.BooleanField(default=False)
    need_teams = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    def game_setting(self):
        return INSTALLED_GAMES_SETTING[self.game_type]

    class Meta:
        ordering = ["session", "game_type", "name"]
        unique_together = [("url_tag", "session"), ("name", "session")]

    def __str__(self):
        return "[{}] {}".format(self.session, self.name)


class Team(models.Model):
    name = models.CharField(max_length=100)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    players = models.ManyToManyField(Player, related_name="teams")
    creator = models.ForeignKey(Player, on_delete=models.CASCADE)

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "game")

    def __str__(self):
        return "[{}] {} - {}".format(self.game.session, self.game.name, self.name)
