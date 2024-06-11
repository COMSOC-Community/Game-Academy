import importlib

from django.db import models
from django.contrib.auth.models import Group, AbstractUser

from core.games import INSTALLED_GAMES_CHOICES, INSTALLED_GAMES


class CustomUser(AbstractUser):
    is_player = models.BooleanField(default=False)
    is_guest_player = models.BooleanField(default=False)

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
    show_create_account = models.BooleanField(default=True)
    show_guest_login = models.BooleanField(default=True)
    show_user_login = models.BooleanField(default=True)
    visible = models.BooleanField(default=False)
    admins = models.ManyToManyField(CustomUser, related_name="administrated_sessions")
    super_admins = models.ManyToManyField(
        CustomUser, related_name="super_administrated_sessions"
    )
    game_after_logging = models.OneToOneField("Game", on_delete=models.CASCADE, related_name="entry_point_of", null=True, blank=True)

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
        Session,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="players",
    )
    is_guest = models.BooleanField(default=False)
    is_team_player = models.BooleanField(default=False)

    def display_name(self):
        if self.is_team_player:
            try:
                return self.represented_team.name
            except Team.DoesNotExist:
                pass
        return self.name

    class Meta:
        ordering = ["session", "name"]
        unique_together = ("name", "session")

    def __str__(self):
        return "[{}] {}".format(self.session, self.name)


class Game(models.Model):
    game_type = models.CharField(
        max_length=100, blank=False, null=False, choices=INSTALLED_GAMES_CHOICES
    )
    name = models.CharField(max_length=100, blank=False, null=False)
    url_tag = models.SlugField(max_length=10, blank=False, null=False)
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, blank=False, null=False, related_name="games"
    )
    playable = models.BooleanField(default=True)
    visible = models.BooleanField(default=False)
    results_visible = models.BooleanField(default=False)
    needs_teams = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    illustration_path = models.CharField(max_length=100, blank=True, null=True)
    ordering_priority = models.IntegerField(help_text="The value used to order the games, the "
                                                      "higher values appear first.",
                                            default=0)
    run_management_after_submit = models.BooleanField(blank=True, null=True)
    initial_view = models.CharField(max_length=50, blank=True, null=True)
    view_after_submit = models.CharField(max_length=50, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Game, self).__init__(*args, **kwargs)

        self.inner_game_config = None

    class Meta:
        ordering = ["session", "-ordering_priority", "game_type", "name"]
        unique_together = [("url_tag", "session"), ("name", "session")]

    def __str__(self):
        return "[{}] {}".format(self.session, self.name)

    def game_config(self):
        if self.inner_game_config is None:
            found = False
            for game_config in INSTALLED_GAMES:
                if game_config.name == self.game_type:
                    self.inner_game_config = game_config
                    found = True
            if not found:
                raise ValueError(
                    f"No configuration for game type {self.game_type} found in the INSTALLED_GAMES "
                    f"list. Something is wrong."
                )
        return self.inner_game_config

    def all_url_names(self):
        urls = getattr(importlib.import_module(f'{self.game_config().name}.urls'), "urlpatterns")
        return tuple(url.name for url in urls)


class Team(models.Model):
    name = models.CharField(max_length=100)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="teams")
    players = models.ManyToManyField(Player, related_name="teams")
    creator = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="created_teams"
    )
    team_player = models.OneToOneField(
        Player, on_delete=models.CASCADE, related_name="represented_team"
    )

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "game")

    def __str__(self):
        return "[{}] {} - {}".format(self.game.session, self.game.name, self.name)
