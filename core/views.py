import logging

from django.contrib.auth import login, logout, authenticate
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import Group
from django.urls import reverse

from .authorisations import can_create_sessions, is_session_admin
from .constants import guest_password, SESSION_GROUP_PREFIX
from .decorators import session_visible_or_admin_decorator, session_admin_decorator
from .forms import (
    LoginForm,
    PlayerLoginForm,
    UserRegistrationForm,
    PlayerRegistrationForm,
    UpdatePasswordForm,
    SessionGuestRegistration,
    SessionFinderForm,
    CreateSessionForm,
    CreateGameForm,
    ModifyGameForm,
    CreateTeamForm,
)
from .models import CustomUser, Session, Player, Game, Team


# ==================
#    ERROR RENDER
# ==================


def error_render(request, template, status):
    response = render(request, template, locals())
    response.status_code = status
    return response


def error_400_view(request, exception):
    return error_render(request, "400.html", 400)


def error_403_view(request, exception):
    return error_render(request, "403.html", 403)


def error_404_view(request, exception):
    return error_render(request, "404.html", 404)


def error_500_view(request):
    return error_render(request, "500.html", 500)


def force_player_logout(request, session_slug_name):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    if request.method == 'POST':
        if 'logout_and_continue' in request.POST:
            logout(request)
            if "next" in request.GET:
                return redirect(request.GET["next"])
            return redirect("core:index")
        else:
            raise Http404("POST request but unknown form type")
    if "prev" in request.GET:
        url_back = request.GET["prev"]
    else:
        url_back = reverse('core:session_home', args=(session.slug_name,))
    return render(request, "core/force_player_logout.html", {"session": session, "url_back": url_back})


# ====================
#    GENERAL INDEX
# ====================

def index(request):
    user_created = False
    user = None
    if request.method == "POST":
        if "session_finder" in request.POST:
            session_finder_form = SessionFinderForm(request.POST)
            if session_finder_form.is_valid():
                return redirect(
                    "core:session_portal",
                    session_slug_name=session_finder_form.cleaned_data[
                        "session_slug_name"
                    ],
                )
            login_form = LoginForm()
            registration_form = UserRegistrationForm()
        elif "login_form" in request.POST:
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                user = authenticate(
                    request,
                    username=login_form.cleaned_data["username"],
                    password=login_form.cleaned_data["password"],
                )
                if user is None:
                    raise Http404("Something went wrong with the login...")
                else:
                    login(request, user)
            session_finder_form = SessionFinderForm()
            registration_form = UserRegistrationForm()
        elif "registration_form" in request.POST:
            registration_form = UserRegistrationForm(request.POST)
            if registration_form.is_valid():
                user = CustomUser.objects.create_user(
                    username=registration_form.cleaned_data["username"],
                    email=registration_form.cleaned_data["email"],
                    password=registration_form.cleaned_data["password1"],
                )
                user_created = True
            session_finder_form = SessionFinderForm()
            login_form = LoginForm()
        else:
            raise Http404("POST request received, but no valid form type was found")
    else:
        session_finder_form = SessionFinderForm()
        login_form = LoginForm()
        registration_form = UserRegistrationForm()

    context = {
        "session_finder_form": session_finder_form,
        "login_form": login_form,
        "registration_form": registration_form,
        "user_created": user_created,
        "user": user,
    }
    return render(request, "core/index.html", context=context)


def logout_user(request):
    logout(request)
    if "next" in request.GET:
        return redirect(request.GET["next"])
    return redirect("core:index")


# ===================
#    SESSION VIEWS
# ===================


def create_session(request):
    user_can_create_session = can_create_sessions(request.user)
    create_session_form = None
    session_obj = None
    session_creation_error = None
    session_created = False
    if user_can_create_session:
        if request.method == "POST":
            create_session_form = CreateSessionForm(request.POST)
            if create_session_form.is_valid():
                session_group = Group.objects.create(
                    name=SESSION_GROUP_PREFIX
                    + str(create_session_form.cleaned_data["slug_name"])
                )
                try:
                    session_obj = Session.objects.create(
                        slug_name=create_session_form.cleaned_data["slug_name"],
                        name=create_session_form.cleaned_data["name"],
                        long_name=create_session_form.cleaned_data["long_name"],
                        can_register=create_session_form.cleaned_data["can_register"],
                        visible=create_session_form.cleaned_data["visible"],
                        group=session_group,
                    )
                    session_obj.admins.add(request.user)
                    session_group.user_set.add(request.user)
                    session_obj.group = session_group
                    create_session_form = CreateSessionForm()
                    session_created = True
                except Exception as e:
                    logger = logging.getLogger("Core_CreateSession")
                    logger.exception("An exception occured while creating a session", e)
                    session_group.delete()
                    session_creation_error = repr(e)
        else:
            create_session_form = CreateSessionForm()

    context = {
        "user_can_create_session": user_can_create_session,
        "create_session_form": create_session_form,
        "session_created": session_created,
        "session_creation_error": session_creation_error,
        "session_obj": session_obj,
    }
    return render(request, "core/create_session.html", context)


@session_visible_or_admin_decorator
def session_portal(request, session_slug_name):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    is_user_admin = is_session_admin(session, request.user)

    authenticated_user = request.user.is_authenticated
    context = {
        "session": session,
        "is_user_admin": is_user_admin,
    }
    if request.method == "POST":
        print(request.POST)
        if "registration_form" in request.POST and session.can_register:
            registration_form = PlayerRegistrationForm(
                request.POST,
                session=session,
                passwords_display=not authenticated_user,
            )
            if registration_form.is_valid():
                if authenticated_user:
                    user = request.user
                else:
                    user = CustomUser.objects.create_user(
                        username=registration_form.cleaned_data["player_username"],
                        password=registration_form.cleaned_data["password1"],
                        is_player=True,
                    )

                try:
                    new_player = Player.objects.create(
                        name=registration_form.cleaned_data["player_name"],
                        user=user,
                        session=session,
                    )
                except Exception as e:
                    # Problem when creating new player, we clean up the mess
                    if not authenticated_user:
                        user.delete()
                    logger = logging.getLogger("Core_SessionPortal")
                    logger.exception("An exception occurred while creating a player", e)
                    context["player_creation_error"] = repr(e)
                if authenticated_user:
                    # If registering a player for a user already logged-in, we redirect to home
                    return redirect("core:session_home", session_slug_name=session.slug_name)
                if "player_creation_error" not in context:
                    # Otherwise we clean the data and stay on the same page
                    context["new_player"] = new_player
            else:
                context["registration_form"] = registration_form
        elif "login_form" in request.POST:
            login_form = PlayerLoginForm(request.POST, session=session)
            if login_form.is_valid():
                user = authenticate(
                    username=login_form.cleaned_data["user"].username,
                    password=login_form.cleaned_data["password"],
                )
                if user:
                    login(request, user)
                    if "player" in login_form.cleaned_data:
                        # If we are loging in a player, we redirected to home
                        return redirect(
                            "core:session_home", session_slug_name=session.slug_name
                        )
                    # If not, we are loging in a user, thus we stay here
                    authenticated_user = True
                # Something weird happened: form is valid but authenticate fails
                context["general_login_error"] = True
            else:
                context["login_form"] = login_form

        elif "guest_form" in request.POST and not session.need_registration:
            guest_form = SessionGuestRegistration(request.POST, session=session)
            if guest_form.is_valid():
                user = CustomUser.objects.create_user(
                    username=guest_form.cleaned_data["guest_username"],
                    password=guest_password(
                        guest_form.cleaned_data["guest_username"]
                    ),
                    is_player=True,
                    is_guest_player=True,
                )

                try:
                    Player.objects.create(
                        name=guest_form.cleaned_data["guest_name"],
                        user=user,
                        session=session,
                        is_guest=True,
                    )
                except Exception as e:
                    # We know the user was initially not authenticated, so we can safely delete it.
                    user.delete()
                    logger = logging.getLogger("Core_SessionPortal")
                    logger.exception("An exception occurred while creating a guest", e)
                    context["guest_creation_error"] = repr(e)
                if "guest_creation_error" not in context:
                    user = authenticate(username=user.username, password=guest_password(user.username))
                    if user:
                        login(request, user)
                        return redirect("core:session_home", session_slug_name=session.slug_name)
                    # Something weird happened: form is valid but authenticate fails
                    context["general_login_error"] = True
            else:
                context["guest_form"] = guest_form
        else:
            raise Http404("POST request received, but no valid form type was found")

    # This value changes when login a user
    context["authenticated_user"] = authenticated_user

    # We put in the context all the forms that are needed and not already in there
    if session.can_register and "registration_form" not in context:
        context["registration_form"] = PlayerRegistrationForm(session=session,
                                                              passwords_display=not authenticated_user)
    if not session.need_registration and "guest_from" not in context:
        context["guest_form"] = SessionGuestRegistration(session=session)
    if authenticated_user:
        player_profile = Player.objects.filter(session=session, user=request.user)
        if player_profile.exists():
            player_profile = player_profile.first()
            context["player_profile"] = player_profile
    elif "login_form" not in context:
        context["login_form"] = PlayerLoginForm(session=session)
    return render(request, "core/session_portal.html", context)


@session_visible_or_admin_decorator
def session_home(request, session_slug_name):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    games = Game.objects.filter(session=session, visible=True)
    admin_user = is_session_admin(session, request.user)

    if admin_user:
        invisible_games = Game.objects.filter(session=session, visible=False)

    if request.user.is_authenticated:
        try:
            player_user = Player.objects.get(session=session, user=request.user)
        except Player.DoesNotExist:
            player_user = None

    return render(request, "core/session_home.html", locals())


@session_admin_decorator
def session_admin(request, session_slug_name):
    session = get_object_or_404(Session, slug_name=session_slug_name)

    context = {}

    # Modify session form
    if request.method == "POST":
        if "modify_session_form" in request.POST:
            modify_session_form = CreateSessionForm(request.POST, session=session)
            if modify_session_form.is_valid():
                session.name = modify_session_form.cleaned_data["name"]
                session.long_name = modify_session_form.cleaned_data["long_name"]
                session.need_registration = modify_session_form.cleaned_data[
                    "need_registration"
                ]
                session.can_register = modify_session_form.cleaned_data[
                    "can_register"
                ]
                session.visible = modify_session_form.cleaned_data["visible"]
                session.save()

                context["session_modified"] = True
                modify_session_form = CreateSessionForm(session=session)
        else:
            raise Http404("POST request but form type unknown.")
    else:
        modify_session_form = CreateSessionForm(session=session)

    context["session"] = session
    context["modify_session_form"] = modify_session_form
    return render(request, "core/session_admin.html", context)


@session_visible_or_admin_decorator
def session_admin_games(request, session_slug_name):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    # Create game form
    if request.method == "POST":
        form_type = request.POST["form_type"]
        if form_type == "create_game_form":
            create_game_form = CreateGameForm(request.POST, session=session)
            if create_game_form.is_valid():
                try:
                    new_game = Game.objects.create(
                        game_type=create_game_form.cleaned_data["game_type"],
                        name=create_game_form.cleaned_data["name"],
                        url_tag=create_game_form.cleaned_data["url_tag"],
                        session=session,
                        playable=create_game_form.cleaned_data["playable"],
                        visible=create_game_form.cleaned_data["visible"],
                        results_visible=create_game_form.cleaned_data[
                            "results_visible"
                        ],
                        need_teams=create_game_form.cleaned_data["need_teams"],
                        description=create_game_form.cleaned_data["description"],
                    )
                    create_game_form = CreateGameForm(session=session)
                    game_created = True
                except Exception as e:
                    game_creation_error = repr(e)
        else:
            create_game_form = CreateGameForm(session=session)
    else:
        create_game_form = CreateGameForm(session=session)

    # Delete game form
    if request.method == "POST":
        form_type = request.POST["form_type"]
        if form_type == "delete_game_form":
            deleted_game_id = request.POST["remove_game_id"]
            deleted_game = Game.objects.get(id=deleted_game_id)
            deleted_game_name = deleted_game.name
            deleted_game.delete()

    games = Game.objects.filter(session=session)

    # Modify game form
    modify_game_forms = []
    for game in games:
        if request.method == "POST":
            form_type = request.POST["form_type"]
            if form_type == "modify_game_form_" + str(game.url_tag):
                modify_game_form = ModifyGameForm(
                    request.POST, session=session, game=game, prefix=game.url_tag
                )
                if modify_game_form.is_valid():
                    game.name = modify_game_form.cleaned_data["name"]
                    game.url_tag = modify_game_form.cleaned_data["url_tag"]
                    game.playable = modify_game_form.cleaned_data["playable"]
                    game.visible = modify_game_form.cleaned_data["visible"]
                    game.results_visible = modify_game_form.cleaned_data[
                        "results_visible"
                    ]
                    game.need_teams = modify_game_form.cleaned_data["need_teams"]
                    game.description = modify_game_form.cleaned_data["description"]
                    game.save()

                    modify_game_form = ModifyGameForm(
                        session=session, game=game, prefix=game.url_tag
                    )

                    modified_game_name = game.name
                    modified_game_form = modify_game_form
            else:
                modify_game_form = ModifyGameForm(
                    session=session, game=game, prefix=game.url_tag
                )
        else:
            modify_game_form = ModifyGameForm(
                session=session, game=game, prefix=game.url_tag
            )
        modify_game_forms.append(modify_game_form)


@session_visible_or_admin_decorator
def session_admin_players(request, session_slug_name):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    # Add player form
    if request.method == "POST":
        form_type = request.POST["form_type"]
        if form_type == "add_player_form":
            add_player_form = PlayerRegistrationForm(request.POST, session=session)
            if add_player_form.is_valid():
                user = CustomUser.objects.create_user(
                    username=add_player_form.cleaned_data["player_username"],
                    password=add_player_form.cleaned_data["password1"],
                    is_player=True,
                )
                try:
                    new_player = Player.objects.create(
                        name=add_player_form.cleaned_data["player_name"],
                        user=user,
                        session=session,
                    )
                    player_added = True
                    add_player_form = PlayerRegistrationForm(session=session)
                except Exception as e:
                    user.delete()
                    add_player_error = e
        else:
            add_player_form = PlayerRegistrationForm(session=session)
    else:
        add_player_form = PlayerRegistrationForm(session=session)

    players = Player.objects.filter(session=session, is_guest=False).exclude(
        user__id__in=session.admins.all()
    )
    guests = Player.objects.filter(session=session, is_guest=True)

    # Delete player form
    if request.method == "POST":
        form_type = request.POST["form_type"]
        if form_type in ("delete_player_form", "delete_guest_form"):
            player_id = request.POST["remove_player_id"]
            player = Player.objects.get(id=player_id)
            if form_type == "delete_player_form":
                deleted_player_name = player.name
            elif form_type == "delete_guest_form":
                delete_guest_name = player.name
            player.user.delete()
            player.delete()

    # Password updates form
    update_password_forms = {}
    if (
        request.method == "POST"
        and request.POST["form_type"] == "update_password_form"
    ):
        player_id = int(request.POST["update_password_player_id"])
        for player in players:
            if player.id == player_id:
                update_password_form = UpdatePasswordForm(
                    request.POST, session=session
                )
                update_password_forms[player] = update_password_form
                if update_password_form.is_valid():
                    player.user.set_password(
                        update_password_form.cleaned_data["password2"]
                    )
                    player.user.save()
                    password_updated_player_name = player.name
            else:
                update_password_forms[player] = UpdatePasswordForm(session=session)
    else:
        for player in players:
            update_password_forms[player] = UpdatePasswordForm(session=session)


def team(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, need_teams=True
    )
    admin_user = is_session_admin(session, request.user)

    if request.user.is_authenticated:
        try:
            player_user = Player.objects.get(session=session, user=request.user)
        except Player.DoesNotExist:
            player_user = None

        teams = Team.objects.filter(game=game)
        if player_user:
            try:
                current_team = player_user.teams.get(game=game)
            except Team.DoesNotExist:
                current_team = None

            if current_team is None:
                if request.method == "POST":
                    form_type = request.POST["form_type"]
                    if form_type == "create_team_form":
                        create_team_form = CreateTeamForm(request.POST, game=game)
                        if create_team_form.is_valid():
                            new_team = Team.objects.create(
                                name=create_team_form.cleaned_data["name"],
                                game=game,
                                creator=player_user,
                            )
                            new_team.players.add(player_user)
                            new_team.save()
                            team_created = True
                    elif form_type == "join_team_form":
                        joined_team = Team.objects.get(
                            pk=request.POST["join_team_input"]
                        )
                        joined_team.players.add(player_user)
                        joined_team.save()
                        team_joined = True
                else:
                    create_team_form = CreateTeamForm(game=game)
        else:
            create_team_form = CreateTeamForm(game=game)

    return render(request, "core/team.html", locals())
