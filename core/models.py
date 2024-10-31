import importlib

from django.db import models
from django.contrib.auth.models import Group, AbstractUser
from django.db.models.signals import post_delete
from django.dispatch import receiver

from core.games import INSTALLED_GAMES_CHOICES, INSTALLED_GAMES


class CustomUser(AbstractUser):
    is_player = models.BooleanField(
        default=False,
        help_text="If True, the user is restricted to their session and cannot access the rest of "
                  "the website."
    )
    is_guest_player = models.BooleanField(
        default=False,
        help_text="If True, the user has joined their session as a guest."
    )
    is_random_player = models.BooleanField(
        default=False,
        help_text="If True, the user has been randomly generated, typically when populating games "
                  "with random answers."
    )

    def display_name(self):
        """Select the right name to display. If the player is a session-restricted user we use
        the name of the player profile."""
        if self.is_player:
            return self.players.first().name
        return self.username

    def __str__(self):
        return self.username


class Session(models.Model):
    url_tag = models.SlugField(
        unique=True,
        max_length=50,
        blank=False,
        null=False,
        help_text="The slug used in the construction of URLs for the session"
    )
    name = models.CharField(
        unique=True,
        max_length=50,
        blank=False,
        null=False,
        help_text="The name of the session, used when there is not much space"
    )
    long_name = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        help_text="The long name of the session, used when space is not constrained"
    )
    show_create_account = models.BooleanField(
        default=True,
        help_text="If True, the users will see the form to create an account to join the session"
    )
    show_guest_login = models.BooleanField(
        default=True,
        help_text="If True, the users will see the form to join the session as a guest"
    )
    show_user_login = models.BooleanField(
        default=True,
        help_text="If True, the users will see the form to login to the session."
    )
    visible = models.BooleanField(
        default=False,
        help_text="If True, the session will be visible to all users and not just admins of the "
                  "sessions"
    )
    admins = models.ManyToManyField(
        CustomUser,
        related_name="administrated_sessions",
        help_text="The admins of the session, i.e., users who have access to management tools."
    )
    super_admins = models.ManyToManyField(
        CustomUser,
        related_name="super_administrated_sessions",
        help_text="The super-admins of the session, i.e., users who have access to advanced "
                  "management tools. This typically includes rights to promote to admin and such."
    )
    game_after_logging = models.OneToOneField(
        "Game",
        on_delete=models.CASCADE,
        related_name="entry_point_of",
        null=True,
        blank=True,
        help_text="If used the selected game will be reached directly after logging instead of the "
                  "home page of the session."
    )
    show_side_panel = models.BooleanField(
        default=True,
        help_text="If False, the side panel will not be displayed."
    )
    show_game_nav_home = models.BooleanField(
        default=True,
        help_text="If False, the 'home' navigation button will not be displayed at the bottom of "
                  "a game page."
    )
    show_game_nav_result = models.BooleanField(
        default=True,
        help_text="If False, the 'result' navigation button will not be displayed at the bottom of "
                  "a game page."
    )

    class Meta:
        ordering = ["url_tag"]

    def __str__(self):
        return f"{self.url_tag} - {self.name}"


class Player(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="players",
        help_text="The user linked to this player. A user can have several player profiles in "
                  "different sessions"
    )
    name = models.SlugField(
        max_length=100,
        blank=False,
        null=False,
        help_text="The name of the player"
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="players",
        help_text="The session the player profile is part of"
    )
    is_team_player = models.BooleanField(
        default=False,
        help_text="If True, the player is acting on behalf of a team. This is a fake player, used "
                  "internally"
    )

    def display_name(self):
        """Select the right way to display the name. In case of a team player, we use the name of
        the team itself."""
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


@receiver(post_delete, sender=Player)
def delete_user_after_player(sender, instance, using, **kwargs):
    """Ensure that when a session-restricted user is deleted, the corresponding user also is
    deleted in an effort to keep the database clean."""
    if not instance.is_team_player:
        user = instance.user
        if user.is_player and user.id is not None:
            user.delete()


class Game(models.Model):
    game_type = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        choices=INSTALLED_GAMES_CHOICES,
        help_text="The type of the game, i.e., the game app it corresponds to"
    )
    name = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        help_text="The name of the game"
    )
    url_tag = models.SlugField(
        max_length=10,
        blank=False,
        null=False,
        help_text="The slug used in the construction of URLs for the game"
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="games",
        help_text="The session the game is part of"
    )
    playable = models.BooleanField(
        default=True,
        help_text="If True the players can submit answers to the game"
    )
    visible = models.BooleanField(
        default=False,
        help_text="If True the game is visible to all players and not just the admins of the "
                  "session."
    )
    results_visible = models.BooleanField(
        default=False,
        help_text="If True the result of the game are visible to all players and not just the "
                  "admins of the session"
    )
    needs_teams = models.BooleanField(
        default=False,
        help_text="If True, players need to first be part of a team before being able to submit an "
                  "answer"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="A description text for the game. Typically a catch-phrase or such."
    )
    illustration_path = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The path to the static file used to illustrate the game"
    )
    ordering_priority = models.IntegerField(
        help_text="The value used to order the games, the higher values appear first.",
        default=0,
    )
    run_management_after_submit = models.BooleanField(
        blank=True,
        null=True,
        help_text="If True the management commands are run directly after each submission"
    )
    initial_view = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The name of the view the users are brought to after accessing the game"
    )
    view_after_submit = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The name of the view the users are brought to after submitting their answer"
    )

    def __init__(self, *args, **kwargs):
        super(Game, self).__init__(*args, **kwargs)

        self.inner_game_config = None

    class Meta:
        ordering = ["session", "-ordering_priority", "game_type", "name"]
        unique_together = [("url_tag", "session"), ("name", "session")]

    def __str__(self):
        return "[{}] {}".format(self.session, self.name)

    def game_config(self):
        """Retrieve the GameConfig linked to this game. This is dictated by the game_type
        parameter. When found for the first time, save the config in the object to avoid searching
        for it again."""
        if self.inner_game_config is None:
            found = False
            for game_config in INSTALLED_GAMES:
                if game_config.name == self.game_type:
                    self.inner_game_config = game_config
                    found = True
                    break
            if not found:
                raise ValueError(
                    f"No configuration for game type {self.game_type} found in the INSTALLED_GAMES "
                    f"list. Something is wrong."
                )
        return self.inner_game_config

    def all_url_names(self):
        """Returns all URL names of the Django app corresponding to the game"""
        urls = getattr(
            importlib.import_module(f"{self.game_config().package_name}.urls"), "urlpatterns"
        )
        return tuple(url.name for url in urls)


class Team(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="The name of the team"
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="teams",
        help_text="The game the team is registered for"
    )
    players = models.ManyToManyField(
        Player,
        related_name="teams",
        help_text="The players that are part of the team",
    )
    is_public = models.BooleanField(
        default=False,
        help_text="If True the team is public and any player can join it. Otherwise, players need "
                  "to know the team's name to join it."
    )
    creator = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="created_teams",
        help_text="The player who created the team"
    )
    team_player = models.OneToOneField(
        Player,
        on_delete=models.CASCADE,
        related_name="represented_team",
        help_text="The internal player used to submit answers for the team"
    )

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "game")

    def __str__(self):
        return "[{}] {} - {}".format(self.game.session, self.game.name, self.name)


@receiver(post_delete, sender=Team)
def delete_team_player_after_team(sender, instance, using, **kwargs):
    """Ensures that when a team is deleted, the corresponding team player also is deleted."""
    instance.team_player.delete()
