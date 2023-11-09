from django import forms
from django.contrib.auth import authenticate

from gameserver.games import INSTALLED_GAMES_CHOICES
from .models import Session, Player, Game, Team, CustomUser
from .constants import player_username, guest_username


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
            self.cleaned_data["session_slug_name"] = session.slug_name
            return session_name
        else:
            raise forms.ValidationError(
                "There is no session named {}.".format(session_name)
            )


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=100,
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
        max_length=100,
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

    def clean_username(self):
        username = self.cleaned_data["username"]

        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "A user with this username already exists. Please choose a different one."
            )

        return username

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
    slug_name = forms.SlugField(
        label="URL tag of the session",
        label_suffix="",
        max_length=Session._meta.get_field("slug_name").max_length,
        help_text="The URL tag is the part of the URL path dedicated to the session. It will "
        "look like /session/SESSION_URL_TAG/. It has to be a 'slug', i.e., it can "
        "only contains letters, numbers, underscores or hyphens.",
        widget=forms.TextInput(attrs={"placeholder": "url_of_session"}),
    )
    name = forms.CharField(
        label="Name of the session",
        label_suffix="",
        max_length=Session._meta.get_field("name").max_length,
        help_text="The name of the session is the name commonly used to refer to the session. It is "
        "typically the string used to find the session on the main page of the website, "
        "or the one showed on the title of the tab in the browser.",
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
    need_registration = forms.BooleanField(
        label="Registration needed",
        label_suffix="",
        initial=True,
        required=False,
        help_text="If registration is needed, only registered players will be able "
        "to play within the session. Otherwise, there will be an option "
        "to play as a guest.",
    )
    can_register = forms.BooleanField(
        label="Registration open",
        label_suffix="",
        initial=False,
        required=False,
        help_text="If the registration is open users can register to the session.",
    )
    visible = forms.BooleanField(
        label="Visible",
        label_suffix="",
        initial=True,
        required=False,
        help_text="If the session is not visible, only admins can see the pages related to "
        "the session. It is useful to prepare things in advance for instance.",
    )

    def clean_slug_name(self):
        slug_name = self.cleaned_data["slug_name"]
        if Session.objects.filter(slug_name=slug_name).exists():
            raise forms.ValidationError(
                "A session with this URL tag already exists. It has to be unique."
            )
        return slug_name

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Session.objects.filter(name=name).exists():
            raise forms.ValidationError(
                "A session with this name already exists. It has to be unique."
            )
        return name

    def clean_long_name(self):
        long_name = self.cleaned_data["long_name"]
        if Session.objects.filter(long_name=long_name).exists():
            raise forms.ValidationError(
                "A session with this long name already exists. It has to be unique."
            )
        return long_name


class PlayerLoginForm(forms.Form):
    player_name = forms.SlugField(
        label="Player name",
        label_suffix="",
        max_length=Player._meta.get_field("name").max_length,
    )
    password = forms.CharField(
        label="Password", label_suffix="", widget=forms.PasswordInput()
    )
    search_user = forms.BooleanField(
        label="Look for users",
        label_suffix="",
        initial=False,
        required=False,
        help_text="If selected, the player name provided is considered to be a username (for a user) instead of the "
        "name of a player for this session.",
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session", None)
        super(PlayerLoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        player_name = self.cleaned_data["player_name"]
        user = None
        print(self.cleaned_data["search_user"])
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
            player_name = player_name.title()
            player = Player.objects.filter(name=player_name, session=self.session)
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
        self.session = kwargs.pop("session", None)
        self.passwords_display = kwargs.pop("passwords_display", True)
        super(PlayerRegistrationForm, self).__init__(*args, **kwargs)
        if not self.passwords_display:
            self.fields.pop("password1")
            self.fields.pop("password2")

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
        player_name = self.cleaned_data["player_name"].title()
        username = player_username(self.session, player_name)
        if CustomUser.objects.filter(
            username=username
        ).exists() or Player.objects.filter(session=self.session, name=player_name):
            raise forms.ValidationError(
                "This player name is already used by someone in this session. Choose another "
                "one."
            )
        self.cleaned_data["player_username"] = username
        return player_name


class UpdatePasswordForm(forms.Form):
    password1 = forms.CharField(
        label="Password",
        label_suffix="",
        widget=forms.PasswordInput(attrs={"placeholder": "New Password"}),
    )
    password2 = forms.CharField(
        label="Repeat password",
        label_suffix="",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat"}),
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session", None)
        super(UpdatePasswordForm, self).__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data["password1"]
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError("The two passwords do not match.")
        return password2


class SessionGuestRegistration(forms.Form):
    guest_name = forms.SlugField(
        label="Guest name",
        label_suffix="",
        max_length=Player._meta.get_field("name").max_length,
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session", None)
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


class ModifySessionForm(forms.Form):
    name = forms.CharField(
        label="Name of the session",
        label_suffix="",
        max_length=Session._meta.get_field("name").max_length,
        help_text="The name of the session is the name commonly used to refer to the session. It is "
        "typically the string used to find the session on the main page of the website, "
        "or the one showed on the title of the tab in the browser.",
    )
    long_name = forms.CharField(
        label="Long name of the session",
        label_suffix="",
        max_length=Session._meta.get_field("long_name").max_length,
        help_text="The long name of the session is a more descriptive title. It is mainly used "
        "in paragraphs, or titles.",
    )
    need_registration = forms.BooleanField(
        label="Registration needed",
        label_suffix="",
        initial=True,
        required=False,
        help_text="If registration is needed, only registered players will be able "
        "to play within the session. Otherwise, there will be an option "
        "to play as a guest.",
    )
    can_register = forms.BooleanField(
        label="Registration open",
        label_suffix="",
        initial=False,
        required=False,
        help_text="If the registration is open users can register to the session.",
    )
    visible = forms.BooleanField(
        label="Visible",
        label_suffix="",
        initial=True,
        required=False,
        help_text="If the session is not visible, only admins can see the pages related to "
        "the session. It is useful to prepare things in advance for instance.",
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session", None)

        kwargs.update(
            initial={
                "name": self.session.name,
                "long_name": self.session.long_name,
                "need_registration": self.session.need_registration,
                "can_register": self.session.can_register,
                "visible": self.session.visible,
            }
        )

        super(ModifySessionForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if name != self.session.name and Session.objects.filter(name=name).exists():
            raise forms.ValidationError(
                "A session with this name already exists. It has to be unique."
            )
        return name

    def clean_long_name(self):
        long_name = self.cleaned_data["long_name"]
        if (
            long_name != self.session.long_name
            and Session.objects.filter(long_name=long_name).exists()
        ):
            raise forms.ValidationError(
                "A session with this long name already exists. It has to be unique."
            )
        return long_name


class CreateGameForm(forms.Form):
    game_type = forms.ChoiceField(
        choices=INSTALLED_GAMES_CHOICES,
        label_suffix="",
        label="Type of Game",
        help_text="Choose the type of game from the list. If the one you are looking for is "
        "not there, contact the administrator to see what can be done.",
    )
    name = forms.CharField(
        label="Name",
        label_suffix="",
        max_length=Game._meta.get_field("name").max_length,
        help_text="The name of the game as will be displayed when referencing to this specific game."
        "It does not have to include the type of game and should typically be a short"
        "string.",
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
    need_teams = forms.BooleanField(
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
        help_text="A brief description of the game displayed on the home page of the "
        "session.",
        widget=forms.Textarea(),
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session", None)
        super(CreateGameForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Game.objects.filter(session=self.session, name=name).exists():
            raise forms.ValidationError(
                "A game with this name already exists for this session."
            )
        else:
            return name

    def clean_url_tag(self):
        url_tag = self.cleaned_data["url_tag"]
        if Game.objects.filter(session=self.session, url_tag=url_tag).exists():
            raise forms.ValidationError(
                "A game with this URL tag already exists for this session."
            )
        else:
            return url_tag


class ModifyGameForm(forms.Form):
    name = forms.CharField(label="Name", label_suffix="", max_length=100)
    url_tag = forms.SlugField(label="URL tag", label_suffix="", max_length=50)
    playable = forms.BooleanField(
        label="Can be played", label_suffix="", required=False, initial=False
    )
    visible = forms.BooleanField(
        label="Is visible", label_suffix="", required=False, initial=False
    )
    results_visible = forms.BooleanField(
        label="Results visible", label_suffix="", required=False, initial=False
    )
    need_teams = forms.BooleanField(
        label="Played in teams", label_suffix="", required=False
    )
    description = forms.CharField(
        label="Description", label_suffix="", widget=forms.Textarea()
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session", None)
        self.game = kwargs.pop("game", None)

        kwargs.update(
            initial={
                "name": self.game.name,
                "url_tag": self.game.url_tag,
                "playable": self.game.playable,
                "visible": self.game.visible,
                "results_visible": self.game.results_visible,
                "need_teams": self.game.need_teams,
                "description": self.game.description,
            }
        )

        super(ModifyGameForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if (
            name != self.game.name
            and Game.objects.filter(session=self.session, name=name).exists()
        ):
            raise forms.ValidationError(
                "A game with this name already exists for this session."
            )
        else:
            return name

    def clean_url_tag(self):
        url_tag = self.cleaned_data["url_tag"]
        if (
            url_tag != self.game.url_tag
            and Game.objects.filter(session=self.session, url_tag=url_tag).exists()
        ):
            raise forms.ValidationError(
                "A game with this URL tag already exists for this session."
            )
        else:
            return url_tag


class CreateTeamForm(forms.Form):
    name = forms.CharField(max_length=Team._meta.get_field("name").max_length)

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop("game", None)
        super(CreateTeamForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Team.objects.filter(game=self.game, name=name).exists():
            raise forms.ValidationError(
                "A team with this name has already been registered for this game."
            )
        else:
            return name
