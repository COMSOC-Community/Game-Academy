import csv
import os
from copy import deepcopy
from io import TextIOWrapper

from django import forms
from django.contrib.auth import authenticate
from django.core.validators import MinValueValidator

from core.games import INSTALLED_GAMES_CHOICES
from core.models import Session, Player, Game, Team, CustomUser
from core.constants import (
    player_username,
    guest_username,
    FORBIDDEN_SESSION_URL_TAGS,
    FORBIDDEN_USERNAMES,
)


class SessionFinderForm(forms.Form):
    session_name = forms.CharField(
        label="Name of the session",
        max_length=Session._meta.get_field("name").max_length,
        widget=forms.TextInput(attrs={"placeholder": "Session name"}),
    )

    def clean_session_name(self):
        session_name = self.cleaned_data["session_name"]
        session = Session.objects.filter(name=session_name)
        if session.exists():
            session = session.first()
            self.cleaned_data["session_url_tag"] = session.url_tag
            return session_name
        else:
            raise forms.ValidationError(
                "There is no session named {}.".format(session_name)
            )


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=CustomUser._meta.get_field("username").max_length,
        widget=forms.TextInput(attrs={"placeholder": "Username"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError(
                    "Invalid username or password. Please try again."
                )
        return cleaned_data


class UserRegistrationForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=CustomUser._meta.get_field("username").max_length,
        widget=forms.TextInput(attrs={"placeholder": "Username"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )
    password2 = forms.CharField(
        label="Repeat Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat password"}),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(UserRegistrationForm, self).__init__(*args, **kwargs)

        if self.user:
            self.fields.pop("email")
            self.fields["username"].disabled = True
            if self.user.is_player:
                self.fields["username"].initial = self.user.players.first().name
            else:
                self.fields["username"].initial = self.user.username

    def clean_username(self):
        username = self.cleaned_data["username"]
        if not self.user:
            if username in FORBIDDEN_USERNAMES:
                raise forms.ValidationError(
                    "This is a forbidden username. Please choose a different username."
                )
            if CustomUser.objects.filter(username=username).exists():
                raise forms.ValidationError(
                    "A user with this username already exists. Please choose a different username."
                )
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not self.user and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "A user with this email address already exists. You can try logging-in."
            )
        return email

    def clean_password1(self):
        password1 = self.cleaned_data["password1"]
        if len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data["password2"]

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match. Please try again.")

        return password2


class CreateSessionForm(forms.Form):
    url_tag = forms.SlugField(
        label="URL tag of the session",
        label_suffix="",
        max_length=Session._meta.get_field("url_tag").max_length,
        help_text="The URL tag is the part of the URL path dedicated to the session. It will "
        "look like /SESSION_URL_TAG/. It has to be a 'slug', i.e., it can "
        "only contains letters, numbers, underscores or hyphens.",
        widget=forms.TextInput(attrs={"placeholder": "url_of_session"}),
    )
    name = forms.CharField(
        label="Name of the session",
        label_suffix="",
        max_length=Session._meta.get_field("name").max_length,
        help_text="The name of the session is the name commonly used to refer to the session. It "
        "is typically the string used to find the session on the main page of the "
        "website, or the one showed on the title of the tab in the browser.",
        widget=forms.TextInput(attrs={"placeholder": "Course2023"}),
    )
    long_name = forms.CharField(
        label="Long name of the session",
        label_suffix="",
        max_length=Session._meta.get_field("long_name").max_length,
        help_text="The long name of the session is a more descriptive title. It is mainly used "
        "in paragraphs, or titles.",
        widget=forms.TextInput(attrs={"placeholder": "The Course, Edition 2023"}),
    )
    show_guest_login = forms.BooleanField(
        label="Guest login available",
        label_suffix="",
        initial=True,
        required=False,
        help_text="If the guest login is available users have the possibility to join the session "
        "as guests, i.e., they do not need to have an account.",
    )
    show_user_login = forms.BooleanField(
        label="User login available",
        label_suffix="",
        initial=True,
        required=False,
        help_text="If the user login is available users have the possibility to join the session by"
        " logging in to their user account.",
    )
    show_create_account = forms.BooleanField(
        label="Registration open",
        label_suffix="",
        initial=False,
        required=False,
        help_text="If the registration is open users can create accounts to join the session.",
    )
    visible = forms.BooleanField(
        label="Visible",
        label_suffix="",
        initial=False,
        required=False,
        help_text="If the session is not visible, only admins can see the pages related to "
        "the session. It is useful to prepare things in advance for instance.",
    )
    game_after_logging = forms.ModelChoiceField(
        label="Game After Login",
        label_suffix="",
        queryset=None,
        required=False,
        help_text="If a value is set, the users are directly brought to the main page of the "
        "selected game after logging in. This means that the session home page is "
        "skipped.",
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop(
            "session", None
        )  # Not none if session is passed, i.e., the form is used to modify a session
        if self.session:
            kwargs.update(
                initial={
                    "url_tag": self.session.url_tag,
                    "name": self.session.name,
                    "long_name": self.session.long_name,
                    "show_guest_login": self.session.show_guest_login,
                    "show_user_login": self.session.show_user_login,
                    "show_create_account": self.session.show_create_account,
                    "visible": self.session.visible,
                    "game_after_logging": self.session.game_after_logging,
                }
            )
        super(CreateSessionForm, self).__init__(*args, **kwargs)
        if self.session:
            self.fields["url_tag"].disabled = True
            games = self.session.games.all()
            if games.exists():
                self.fields["game_after_logging"].queryset = games
            else:
                self.fields.pop("game_after_logging")
        else:
            self.fields.pop("game_after_logging")

    def clean_url_tag(self):
        url_tag = self.cleaned_data["url_tag"]
        if not self.session and Session.objects.filter(url_tag=url_tag).exists():
            raise forms.ValidationError(
                "A session with this URL tag already exists. It has to be unique."
            )
        if url_tag in FORBIDDEN_SESSION_URL_TAGS:
            raise forms.ValidationError(
                "This url_tag cannot be used for a session. Choose another one."
            )
        return url_tag

    def clean_name(self):
        name = self.cleaned_data["name"]
        new_name = not self.session or name != self.session.name
        if new_name and Session.objects.filter(name=name).exists():
            raise forms.ValidationError(
                "A session with this name already exists. It has to be unique."
            )
        return name

    def clean_long_name(self):
        long_name = self.cleaned_data["long_name"]
        new_long_name = not self.session or long_name != self.session.long_name
        if new_long_name and Session.objects.filter(long_name=long_name).exists():
            raise forms.ValidationError(
                "A session with this long name already exists. It has to be unique."
            )
        return long_name


class DeleteSessionForm(forms.Form):
    delete = forms.BooleanField(
        label="Delete the session", label_suffix="", initial=False
    )
    password = forms.CharField(
        label="Your Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(DeleteSessionForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        user = authenticate(username=self.user.username, password=password)
        if not user:
            raise forms.ValidationError("The password is incorrect.")


class PlayerLoginForm(forms.Form):
    player_name = forms.SlugField(
        label="Player name",
        label_suffix="",
        max_length=Player._meta.get_field("name").max_length,
        help_text="This is NOT case sensitive.",
    )
    password = forms.CharField(
        label="Password", label_suffix="", widget=forms.PasswordInput()
    )
    search_user = forms.BooleanField(
        label="Look for users",
        label_suffix="",
        initial=False,
        required=False,
        help_text="If selected, the player name provided is considered to be a username (for a "
        "user) instead of the name of a player for this session.",
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session")
        super(PlayerLoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if "player_name" in self.cleaned_data:
            player_name = self.cleaned_data["player_name"]
            user = None
            if self.cleaned_data["search_user"]:
                user = CustomUser.objects.filter(username=player_name)
                if user.exists():
                    user = user.first()
                    self.cleaned_data["user"] = user
                    player = Player.objects.filter(user=user, session=self.session)
                    if player.exists():
                        self.cleaned_data["player"] = player.first()
                else:
                    raise forms.ValidationError("No match was found.")
            else:
                player = Player.objects.filter(
                    name__iexact=player_name, session=self.session
                )
                if player.exists():
                    player = player.first()
                    user = player.user
                    self.cleaned_data["player"] = player
                    self.cleaned_data["user"] = user
                else:
                    self.add_error(
                        "player_name",
                        forms.ValidationError(
                            "No player with this name is registered for this session."
                        ),
                    )

            if user:
                password = self.cleaned_data["password"]
                user = authenticate(username=user.username, password=password)
                if not user:
                    self.add_error(
                        "password", forms.ValidationError("The password is incorrect.")
                    )


class PlayerRegistrationForm(forms.Form):
    player_name = forms.SlugField(
        label="Player name",
        label_suffix="",
        max_length=Player._meta.get_field("name").max_length,
    )
    password1 = forms.CharField(
        label="Password", label_suffix="", widget=forms.PasswordInput()
    )
    password2 = forms.CharField(
        label="Repeat password", label_suffix="", widget=forms.PasswordInput()
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session")
        self.passwords_display = kwargs.pop("passwords_display", True)
        self.player = kwargs.pop("player", None)
        super(PlayerRegistrationForm, self).__init__(*args, **kwargs)
        if not self.passwords_display:
            self.fields.pop("password1")
            self.fields.pop("password2")
        if self.player:
            self.fields["player_name"].initial = self.player.name
            self.fields["player_name"].disabled = True

    def clean_password1(self):
        password1 = self.cleaned_data["password1"]
        if len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data["password2"]

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match. Please try again.")

        return password2

    def clean_player_name(self):
        player_name = self.cleaned_data["player_name"]
        if not self.player:
            username = player_username(self.session, player_name)
            if (
                CustomUser.objects.filter(username=username).exists()
                or Player.objects.filter(
                    session=self.session, name__iexact=player_name
                ).exists()
            ):
                raise forms.ValidationError(
                    "This player name is already used by someone in this session. Choose another "
                    "one."
                )
            self.cleaned_data["player_username"] = username
        return player_name


class SessionGuestRegistration(forms.Form):
    guest_name = forms.SlugField(
        label="Guest name",
        label_suffix="",
        max_length=Player._meta.get_field("name").max_length,
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session")
        super(SessionGuestRegistration, self).__init__(*args, **kwargs)

    def clean_guest_name(self):
        guest_name = self.cleaned_data["guest_name"]
        username = guest_username(self.session, guest_name)
        if (
            CustomUser.objects.filter(username=username).exists()
            or Player.objects.filter(name=guest_name).exists()
        ):
            raise forms.ValidationError(
                "This guest name is already used by someone in this session. Choose another "
                "one."
            )
        else:
            self.cleaned_data["guest_username"] = username
            return guest_name


class CreateGameForm(forms.Form):
    game_type = forms.ChoiceField(
        choices=[],
        label_suffix="",
        label="Type of Game",
        help_text="Choose the type of game from the list. If the one you are looking for is "
        "not there, contact the administrator to see what can be done.",
    )
    name = forms.CharField(
        label="Name",
        label_suffix="",
        max_length=Game._meta.get_field("name").max_length,
        help_text="The name of the game as will be displayed when referencing to this specific "
        "game. It typically is the name of the game (e.g., 'Numbers Game').",
    )
    url_tag = forms.SlugField(
        label="URL tag",
        label_suffix="",
        max_length=Game._meta.get_field("url_tag").max_length,
        help_text="The URL tag is the part of the URL path dedicated to the game. It will "
        "look like /session/SESSION_URL_TAG/GAME_TYPE_URL_TAG/GAME_URL_TAG. It has to "
        "be a 'slug', i.e., it can only contains letters, numbers, underscores or "
        "hyphens.",
    )
    visible = forms.BooleanField(
        label="Is visible",
        label_suffix="",
        required=False,
        initial=False,
        help_text="If not visible, only admins can see the game.",
    )
    playable = forms.BooleanField(
        label="Can be played",
        label_suffix="",
        required=False,
        initial=False,
        help_text="If set to no, players cannot submit their answers to the game. This is "
        "how one can close a game.",
    )
    results_visible = forms.BooleanField(
        label="Results visible",
        label_suffix="",
        required=False,
        initial=False,
        help_text="When set to True, the players will be able to access the result "
        "page of the game.",
    )
    needs_teams = forms.BooleanField(
        label="Played in teams",
        label_suffix="",
        required=False,
        help_text="Setting this to true will allow players to register teams for this "
        "game.",
    )
    description = forms.CharField(
        label="Description",
        label_suffix="",
        required=False,
        help_text="A brief description of the game displayed on the home page of the session. "
        "It is typically either empty or a short sentence.",
        widget=forms.Textarea(),
    )
    illustration_path = forms.ChoiceField(
        label="Illustration",
        label_suffix="",
        required=False,
        help_text="The image used to illustrate the game. Unfortunately there is no nice display "
        "for you to see them before updating the game.",
    )
    ordering_priority = forms.IntegerField(
        label="Ordering Priority",
        label_suffix="",
        required=False,
        help_text="The value used to order the games, the higher values appear first. If no value "
        "is provided when creating a game, the new game is given the highest priority "
        "plus 1.",
    )
    run_management_after_submit = forms.BooleanField(
        label="Automatic Management Commands",
        label_suffix="",
        required=False,
        help_text="If selected the management commands will be run each time an answer is "
        "submitted. This means that the administrator will not have to run them manually."
        "Selecting this can induce delays for the users of the website.",
    )
    initial_view = forms.ChoiceField(
        label="Main Page",
        label_suffix="",
        required=False,
        help_text="The first page accessed by a user when clicking on a link to the game. The "
        "default is the home page of the game. You can use this setting to directly "
        "bring the users to the answer page for instance.",
    )
    view_after_submit = forms.ChoiceField(
        label="Page After Submit",
        label_suffix="",
        required=False,
        help_text="The page that the user is redirected to after having submitted an answer. The "
        "default is the main page of the game (see the main page setting). You can use "
        "this setting to bring the users to the results page directly after submitting "
        "for instance.",
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session")
        self.game = kwargs.pop("game", None)
        if self.game:
            kwargs.update(
                initial={
                    "game_type": self.game.game_type,
                    "name": self.game.name,
                    "url_tag": self.game.url_tag,
                    "playable": self.game.playable,
                    "visible": self.game.visible,
                    "results_visible": self.game.results_visible,
                    "needs_teams": self.game.needs_teams,
                    "description": self.game.description,
                    "illustration_path": self.game.illustration_path,
                    "ordering_priority": self.game.ordering_priority,
                    "run_management_after_submit": self.game.run_management_after_submit,
                    "initial_view": self.game.initial_view,
                    "view_after_submit": self.game.view_after_submit,
                }
            )

        super(CreateGameForm, self).__init__(*args, **kwargs)

        # Needed here because of the apps are only registered after their ready method.
        self.fields["game_type"].choices = INSTALLED_GAMES_CHOICES

        if self.game:
            illustration_choices = [
                (i, os.path.splitext(os.path.basename(i))[0])
                for i in self.game.game_config().illustration_paths
            ]
            self.fields["illustration_path"].choices = illustration_choices
            all_views = [(u, u) for u in self.game.all_url_names()]
            self.fields["initial_view"].choices = all_views
            self.fields["view_after_submit"].choices = all_views
            self.fields["game_type"].disabled = True
        else:
            self.fields.pop("illustration_path")
            self.fields.pop("ordering_priority")
            self.fields.pop("run_management_after_submit")
            self.fields.pop("initial_view")
            self.fields.pop("view_after_submit")

    def clean_name(self):
        name = self.cleaned_data["name"]
        new_name = not self.game or name != self.game.name
        if new_name and Game.objects.filter(session=self.session, name=name).exists():
            raise forms.ValidationError(
                "A game with this name already exists for this session."
            )
        return name

    def clean_url_tag(self):
        url_tag = self.cleaned_data["url_tag"]
        new_url_tag = not self.game or url_tag != self.game.url_tag
        if (
            new_url_tag
            and Game.objects.filter(session=self.session, url_tag=url_tag).exists()
        ):
            raise forms.ValidationError(
                "A game with this URL tag already exists for this session."
            )
        else:
            return url_tag


def validate_csv_file(value):
    value = deepcopy(value)
    if not value.name.endswith(".csv"):
        raise forms.ValidationError(
            "Only CSV files are allowed (extension must be '.csv')."
        )
    try:
        csv_reader = csv.reader(TextIOWrapper(value))
        header = next(csv_reader, None)
        if header is None:
            raise forms.ValidationError("CSV file must have a header row.")
        num_columns = len(header)
        for row in csv_reader:
            if row:
                if len(row) != num_columns:
                    raise forms.ValidationError(
                        "All rows must have the same number of columns as"
                        " the header."
                    )

    except csv.Error as e:
        raise forms.ValidationError(f"Error reading CSV file: {e}")


class ImportCSVFileForm(forms.Form):
    csv_file = forms.FileField(
        label="Upload CSV File",
        validators=[validate_csv_file],
        widget=forms.ClearableFileInput(attrs={"accept": ".csv"}),
    )

    def clean_csv_file(self):
        uploaded_file = self.cleaned_data["csv_file"]
        if not uploaded_file.name.endswith(".csv"):
            raise forms.ValidationError(
                "Only CSV files are allowed (extension must be '.csv')."
            )
        return uploaded_file


class RandomPlayersForm(forms.Form):
    num_players = forms.IntegerField(
        label="Number of players", label_suffix="", validators=[MinValueValidator(1)]
    )


class RandomAnswersForm(forms.Form):
    num_answers = forms.IntegerField(
        label="Number of answers", label_suffix="", validators=[MinValueValidator(1)]
    )
    run_management = forms.BooleanField(
        label="Run management commands",
        label_suffix="",
        help_text="If selected, the management commands are executed after the answers have been generated.",
        required=False,
    )


class MakeAdminForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=CustomUser._meta.get_field("username").max_length,
        required=False,
        help_text="The username of the user you want to make admin. be mindful of the difference "
        "between a player and a user. Only one fo the 'username' and the 'player name' "
        "field should be filled in.",
    )
    playername = forms.CharField(
        label="Player name",
        max_length=CustomUser._meta.get_field("username").max_length,
        required=False,
        help_text="The player name of the user you want to make admin. be mindful of the "
        "difference between a player and a user. Only one fo the 'username' and the "
        "'player name' field should be filled in.",
    )
    super_admin = forms.BooleanField(
        label="Super admin",
        label_suffix="",
        required=False,
        help_text="If ticked, the user will be made super-admin, meaning, among others, that they "
        "will be able to manage admins.",
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session")
        super(MakeAdminForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        playername = cleaned_data.get("playername")
        if not username and not playername:
            raise forms.ValidationError(
                "You need to input either a username or a player name."
            )
        if username and playername:
            raise forms.ValidationError(
                "You cannot provide both a username and a player name, choose one."
            )
        if username:
            try:
                user = CustomUser.objects.get(username=username)
                cleaned_data["user"] = user
            except CustomUser.DoesNotExist:
                self.add_error(
                    "username",
                    forms.ValidationError(
                        "This username has not been found in the database."
                    ),
                )
        if playername:
            try:
                player = Player.objects.get(name=playername, session=self.session)
                cleaned_data["user"] = player.user
            except Player.DoesNotExist:
                self.add_error(
                    "playername",
                    forms.ValidationError(
                        "No player with this name is registered for this session."
                    ),
                )
        return cleaned_data


class CreateTeamForm(forms.Form):
    name = forms.CharField(max_length=Team._meta.get_field("name").max_length)

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop("game")
        super(CreateTeamForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Team.objects.filter(game=self.game, name=name).exists():
            raise forms.ValidationError(
                "A team with this name has already been registered for this game."
            )
        else:
            return name
