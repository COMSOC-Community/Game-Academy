import logging

from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.core import management
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .authorisations import (
    can_create_sessions,
    is_session_admin,
    is_session_super_admin,
)
from .constants import guest_password
from .decorators import session_admin_decorator
from .forms import (
    LoginForm,
    PlayerLoginForm,
    UserRegistrationForm,
    PlayerRegistrationForm,
    SessionGuestRegistration,
    SessionFinderForm,
    CreateSessionForm,
    CreateGameForm,
    CreateTeamForm,
    DeleteSessionForm,
    MakeAdminForm,
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


# ===================
#    SPECIAL VIEWS
# ===================


def validate_next_url(request, next_url):
    return url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


def force_player_logout(request, session_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    if request.method == "POST":
        if "logout_and_continue" in request.POST:
            logout(request)
            if "next" in request.GET:
                next_url = request.GET["next"]
                if validate_next_url(request, next_url):
                    return redirect(next_url)
            return redirect("core:index")
        else:
            raise Http404("POST request but unknown form type")

    url_back = reverse("core:session_home", args=(session.url_tag,))
    if "prev" in request.GET:
        prev_url = request.GET["prev"]
        if url_has_allowed_host_and_scheme(
            url=prev_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            url_back = prev_url
    return render(
        request,
        "core/force_player_logout.html",
        {"session": session, "url_back": url_back},
    )


def message(request):
    context = {
        "next_url": reverse("core:index"),
        "message": request.session.pop(
            "_message_view_message", "This is the default message"
        ),
    }
    next_url = request.session.pop("_message_view_next_url", None)
    if next_url:
        if validate_next_url(request, next_url):
            context["next_url"] = next_url
    return render(request, "core/message.html", context)


# ==========================
#    CONTEXT INITIALISERS
# ==========================

def base_context_initialiser(request, context=None):
    if context is None:
        context = {}
    context["user_is_authenticated"] = request.user.is_authenticated
    if context["user_is_authenticated"]:
        user = request.user
        context["user"] = user
        context["user_is_only_player"] = user.is_player
        context["user_is_only_guest"] = user.is_guest_player
        if not context["user_is_only_player"]:
            context["user_administrated_sessions"] = user.administrated_sessions.all()
            context["user_player_sessions"] = []
            for player in user.players.all():
                if player.session not in context["user_administrated_sessions"]:
                    context["user_player_sessions"].append(player.session)
    return context


def session_context_initialiser(request, session, context=None):
    if context is None:
        context = {}
    context["session"] = session
    if request.user.is_authenticated:
        context["user_is_session_admin"] = is_session_admin(session, request.user)
    return context


def game_context_initialiser(request, session, game, context=None):
    if context is None:
        context = {}
    context["game"] = game
    return context


# ====================
#    GENERAL INDEX
# ====================


def index(request):
    context = base_context_initialiser(request)

    login_form = LoginForm()
    registration_form = UserRegistrationForm()
    session_finder_form = SessionFinderForm()
    if request.method == "POST":
        if "session_finder" in request.POST:
            session_finder_form = SessionFinderForm(request.POST)
            if session_finder_form.is_valid():
                return redirect(
                    "core:session_portal",
                    session_url_tag=session_finder_form.cleaned_data["session_url_tag"],
                )
        elif "login_form" in request.POST:
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                user = authenticate(
                    request,
                    username=login_form.cleaned_data["username"],
                    password=login_form.cleaned_data["password"],
                )
                if user is None:
                    # Something weird happened: form is valid but authenticate fails
                    context["general_login_error"] = True
                else:
                    login(request, user)
                    return redirect("core:index")
        elif "registration_form" in request.POST:
            registration_form = UserRegistrationForm(request.POST)
            if registration_form.is_valid():
                user = CustomUser.objects.create_user(
                    username=registration_form.cleaned_data["username"],
                    email=registration_form.cleaned_data["email"],
                    password=registration_form.cleaned_data["password1"],
                )
                context["created_user"] = user
        else:
            raise Http404("POST request received, but no valid form type was found")

    context["session_finder_form"] = session_finder_form
    context["login_form"] = login_form
    context["registration_form"] = registration_form

    return render(request, "core/index.html", context=context)


# ================
#    USER VIEWS
# ================


def logout_user(request):
    logout(request)
    next_url = request.GET.get("next")
    if next_url:
        if validate_next_url(request, next_url):
            return redirect(next_url)
    return redirect("core:index")


def user_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.user != user:
        raise Http404("This page is not the business of the logged-in user.")
    return render(request, "core/user_profile.html")


def change_password(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.user != user:
        raise Http404("This page is not the business of the logged-in user.")

    update_password_form = UserRegistrationForm(user=user)
    if request.method == "POST" and "update_password_form" in request.POST:
        update_password_form = UserRegistrationForm(request.POST, user=user)
        if update_password_form.is_valid():
            request.user.set_password(update_password_form.cleaned_data["password1"])
            request.user.save()
            update_session_auth_hash(request, request.user)
            request.session[
                "_message_view_message"
            ] = f"Your password has been changed."
            if request.user.is_player:
                return redirect("core:session_home", session_url_tag=request.user.players.first().session.url_tag)
            return redirect("core:message")

    context = base_context_initialiser(request)
    context["update_password_form"] = update_password_form
    return render(request, "core/change_password.html", context)


# ===========================
#    GENERAL SESSION VIEWS
# ===========================


def create_session(request):
    user_can_create_session = can_create_sessions(request.user)
    if not user_can_create_session:
        raise Http404("This user cannot create sessions.")

    context = base_context_initialiser(request)
    create_session_form = CreateSessionForm()
    if request.method == "POST":
        if "create_session_form" in request.POST:
            create_session_form = CreateSessionForm(request.POST)
            if create_session_form.is_valid():
                session_obj = Session.objects.create(
                    url_tag=create_session_form.cleaned_data["url_tag"],
                    name=create_session_form.cleaned_data["name"],
                    long_name=create_session_form.cleaned_data["long_name"],
                    can_register=create_session_form.cleaned_data["can_register"],
                    visible=create_session_form.cleaned_data["visible"],
                )
                session_obj.admins.add(request.user)
                session_obj.super_admins.add(request.user)
                create_session_form = CreateSessionForm()
                context["created_session"] = session_obj
        else:
            raise Http404("POST request received but form type unknown.")
    context["create_session_form"] = create_session_form
    return render(request, "core/create_session.html", context)


def session_portal(request, session_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)

    context = base_context_initialiser(request)
    context["session"] = session

    authenticated_user = request.user.is_authenticated
    is_user_admin = is_session_admin(session, request.user)
    if is_user_admin:
        session_context_initialiser(request, session, context)

    if request.method == "POST":
        if "registration_form" in request.POST and session.can_register:
            registration_form = PlayerRegistrationForm(
                request.POST,
                session=session,
                passwords_display=not authenticated_user,
            )
            if registration_form.is_valid():
                # If user is not already authenticated, we need to create one
                if authenticated_user:
                    user = request.user
                else:
                    user = CustomUser.objects.create_user(
                        username=registration_form.cleaned_data["player_username"],
                        password=registration_form.cleaned_data["password1"],
                        is_player=True,
                    )

                try:
                    created_player = Player.objects.create(
                        name=registration_form.cleaned_data["player_name"],
                        user=user,
                        session=session,
                    )
                    # If user already logged-in we go to session home, otherwise we stay
                    if authenticated_user:
                        return redirect(
                            "core:session_home", session_url_tag=session.url_tag
                        )
                    context["created_player"] = created_player
                except Exception as e:
                    # Problem when creating new player, we clean up the mess
                    context["player_creation_error"] = repr(e)
                    if not authenticated_user:
                        user.delete()
                    logger = logging.getLogger("Core_SessionPortal")
                    logger.exception("An exception occurred while creating a player", e)

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
                            "core:session_home", session_url_tag=session.url_tag
                        )
                    # If not, we are loging in a user, thus we stay here
                    return redirect("core:session_portal", session_url_tag=session.url_tag)
                # Something weird happened: form is valid but authenticate fails
                context["general_login_error"] = True
            else:
                context["login_form"] = login_form

        elif "guest_form" in request.POST and not session.need_registration:
            guest_form = SessionGuestRegistration(request.POST, session=session)
            if guest_form.is_valid():
                user = CustomUser.objects.create_user(
                    username=guest_form.cleaned_data["guest_username"],
                    password=guest_password(guest_form.cleaned_data["guest_username"]),
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
                    user = authenticate(
                        username=user.username, password=guest_password(user.username)
                    )
                    if user:
                        login(request, user)
                        return redirect(
                            "core:session_home", session_url_tag=session.url_tag
                        )
                    # Something weird happened: form is valid but authenticate fails
                    context["general_login_error"] = True
                except Exception as e:
                    if not authenticated_user:
                        user.delete()
                    logger = logging.getLogger("Core_SessionPortal")
                    logger.exception("An exception occurred while creating a guest", e)
                    context["guest_creation_error"] = repr(e)
            else:
                context["guest_form"] = guest_form
        else:
            raise Http404("POST request received, but no valid form type was found")

    # We put in the context all the forms that are needed and not already in there
    if session.can_register and "registration_form" not in context:
        context["registration_form"] = PlayerRegistrationForm(
            session=session, passwords_display=not authenticated_user
        )
    if not session.need_registration and "guest_form" not in context:
        context["guest_form"] = SessionGuestRegistration(session=session)
    if authenticated_user:
        player_profile = Player.objects.filter(session=session, user=request.user)
        if player_profile.exists():
            player_profile = player_profile.first()
            context["player_profile"] = player_profile
    elif "login_form" not in context:
        context["login_form"] = PlayerLoginForm(session=session)
    return render(request, "core/session_portal.html", context)


def session_home(request, session_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    games = Game.objects.filter(session=session, visible=True)
    admin_user = is_session_admin(session, request.user)

    context = {"session": session, "games": games, "admin_user": admin_user}

    if admin_user:
        context["invisible_games"] = Game.objects.filter(session=session, visible=False)

    if request.user.is_player:
        context["player_profile"] = request.user.players.first()

    return render(request, "core/session_home.html", locals())


# =========================
#    ADMIN SESSION VIEWS
# =========================


@session_admin_decorator
def session_admin(request, session_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)

    context = {}

    # Modify session form
    modify_session_form = CreateSessionForm(session=session)
    delete_session_form = DeleteSessionForm(user=request.user)
    if request.method == "POST":
        if "modify_session_form" in request.POST:
            modify_session_form = CreateSessionForm(request.POST, session=session)
            if modify_session_form.is_valid():
                session.name = modify_session_form.cleaned_data["name"]
                session.long_name = modify_session_form.cleaned_data["long_name"]
                session.need_registration = modify_session_form.cleaned_data[
                    "need_registration"
                ]
                session.can_register = modify_session_form.cleaned_data["can_register"]
                session.visible = modify_session_form.cleaned_data["visible"]
                session.save()

                context["session_modified"] = True
                modify_session_form = CreateSessionForm(session=session)
        elif "delete_session_form" in request.POST:
            delete_session_form = DeleteSessionForm(request.POST, user=request.user)
            if delete_session_form.is_valid():
                request.session[
                    "_message_view_message"
                ] = f"The session {session.name} has been deleted."
                request.session["_message_view_next_url"] = reverse("core:index")
                session.delete()
                return redirect("core:message")
        else:
            raise Http404("POST request but form type unknown.")

    context["session"] = session
    context["modify_session_form"] = modify_session_form
    context["delete_session_form"] = delete_session_form
    return render(request, "core/session_admin.html", context)


@session_admin_decorator
def session_admin_games(request, session_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    context = {"session": session}

    # Create game form
    create_game_form = CreateGameForm(session=session)
    if request.method == "POST" and "create_game_form" in request.POST:
        create_game_form = CreateGameForm(request.POST, session=session)
        if create_game_form.is_valid():
            new_game = Game.objects.create(
                game_type=create_game_form.cleaned_data["game_type"],
                name=create_game_form.cleaned_data["name"],
                url_tag=create_game_form.cleaned_data["url_tag"],
                session=session,
                playable=create_game_form.cleaned_data["playable"],
                visible=create_game_form.cleaned_data["visible"],
                results_visible=create_game_form.cleaned_data["results_visible"],
                need_teams=create_game_form.cleaned_data["need_teams"],
                description=create_game_form.cleaned_data["description"],
            )
            create_game_form = CreateGameForm(session=session)
            context["new_game"] = new_game

            game_config = new_game.game_config()
            if game_config.setting_model is not None:
                game_config.setting_model.objects.create(game=new_game)

    # Delete game form
    if request.method == "POST" and "delete_game_form" in request.POST:
        deleted_game_id = request.POST["remove_game_id"]
        deleted_game = Game.objects.get(id=deleted_game_id)
        deleted_game.delete()
        context["deleted_game_name"] = deleted_game.name

    games = Game.objects.filter(session=session)

    # Modify game form
    modify_game_forms = []
    for game in games:
        modify_game_form = CreateGameForm(
            session=session, game=game, prefix=game.url_tag
        )
        modify_game_setting_form = None
        if game.game_config().setting_form is not None:
            setting_model = game.game_config().setting_model
            game_setting_obj = getattr(
                game, setting_model._meta.get_field("game").related_query_name()
            )
            modify_game_setting_form = game.game_config().setting_form(
                instance=game_setting_obj
            )
        if request.method == "POST":
            if "modify_game_form_" + str(game.url_tag) in request.POST:
                modify_game_form = CreateGameForm(
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

                    modify_game_form = CreateGameForm(
                        session=session, game=game, prefix=game.url_tag
                    )
                    context["modified_game"] = game
            elif "modify_game_setting_form_" + str(game.url_tag) in request.POST:
                setting_model = game.game_config().setting_model
                game_setting_obj = getattr(
                    game, setting_model._meta.get_field("game").related_query_name()
                )
                modify_game_setting_form = game.game_config().setting_form(
                    request.POST, instance=game_setting_obj
                )
                if modify_game_setting_form.is_valid():
                    modify_game_setting_form.save()
                modify_game_setting_form = game.game_config().setting_form(
                    instance=game_setting_obj
                )
        modify_game_forms.append((modify_game_form, modify_game_setting_form))

    context["create_game_form"] = create_game_form
    context["modify_game_forms"] = modify_game_forms
    return render(request, "core/session_admin_games.html", context)


@session_admin_decorator
def session_admin_players(request, session_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    is_user_super_admin = is_session_super_admin(session, request.user)
    context = {"session": session, "is_user_super_admin": is_user_super_admin}

    # Add player form
    add_player_form = PlayerRegistrationForm(session=session)
    if request.method == "POST" and "add_player_form" in request.POST:
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
                context["new_player"] = new_player
                add_player_form = PlayerRegistrationForm(session=session)
            except Exception as e:
                user.delete()
                logger = logging.getLogger("Core_SessionPortal")
                logger.exception("An exception occurred while creating a player", e)
                context["player_creation_error"] = True
    context["add_player_form"] = add_player_form

    players = Player.objects.filter(session=session, is_guest=False)
    guests = Player.objects.filter(session=session, is_guest=True)

    # Delete player form
    if request.method == "POST" and (
        "delete_player_form" in request.POST or "delete_guest_form" in request.POST
    ):
        player_id = request.POST["remove_player_id"]
        player = Player.objects.get(id=player_id)
        if "delete_player_form" in request.POST:
            context["deleted_player_name"] = player.name
        elif "delete_guest_form" in request.POST:
            context["deleted_guest_name"] = player.name
        player.user.delete()
        player.delete()

    # Make admin form
    if is_user_super_admin:
        make_admin_form = MakeAdminForm(session=session)
        if request.method == "POST" and "make_admin_form" in request.POST:
            make_admin_form = MakeAdminForm(request.POST, session=session)
            if make_admin_form.is_valid():
                user = make_admin_form.cleaned_data["user"]
                session.admins.add(user)
                if make_admin_form.cleaned_data["super_admin"]:
                    session.super_admins.add(user)
                make_admin_form = MakeAdminForm(session=session)
                context["new_admin"] = user
        context["make_admin_form"] = make_admin_form

    # Remove admin form
    if is_user_super_admin:
        if request.method == "POST" and "remove_admin_form" in request.POST:
            admin_id = request.POST["remove_admin_id"]
            admin = CustomUser.objects.get(id=admin_id)
            session.super_admins.remove(admin)
            session.admins.remove(admin)
            context["removed_admin"] = admin

    super_admins = session.super_admins.all()
    admins = session.admins.exclude(id__in=super_admins)
    context["super_admins"] = super_admins
    context["admins"] = admins

    context["players"] = players
    context["guests"] = guests
    return render(request, "core/session_admin_players.html", context)


@session_admin_decorator
def session_admin_player_password(request, session_url_tag, player_name):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    player = get_object_or_404(Player, session=session, name=player_name.title())
    context = {"session": session, "player": player}

    update_password_form = PlayerRegistrationForm(session=session, player=player)
    if request.method == "POST" and "update_password_form" in request.POST:
        update_password_form = PlayerRegistrationForm(
            request.POST, session=session, player=player
        )
        if update_password_form.is_valid():
            player.user.set_password(update_password_form.cleaned_data["password1"])
            player.user.save()
            update_session_auth_hash(request, player.user)
    context["update_password_form"] = update_password_form
    return render(request, "core/session_admin_player_password.html", context)


# ================
#    TEAM VIEWS
# ================


def team(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
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


# ======================
#    ADMIN GAME VIEWS
# ======================


def quick_game_admin_render(request, session, game, info_message):
    request.session["_message_view_message"] = info_message
    if "next" in request.GET:
        request.session["_message_view_next_url"] = request.GET["next"]
    else:
        request.session["_message_view_next_url"] = reverse(
            game.game_config().url_namespace + ":index",
            kwargs={"session_url_tag": session.url_tag, "game_url_tag": game.url_tag},
        )
    return redirect("core:message")


@session_admin_decorator
def game_play_toggle(request, session_url_tag, game_url_tag, game_type):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=game_type
    )
    game.playable = not game.playable
    game.save()
    if game.playable:
        info_message = "Players can now submit their answers."
    else:
        info_message = "Players can no longer submit answers."
    return quick_game_admin_render(request, session, game, info_message)


@session_admin_decorator
def game_result_toggle(request, session_url_tag, game_url_tag, game_type):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=game_type
    )
    game.results_visible = not game.results_visible
    game.save()

    if game.results_visible:
        info_message = "Players can now see the results."
    else:
        info_message = "Players can no longer see the results."
    return quick_game_admin_render(request, session, game, info_message)


@session_admin_decorator
def game_run_management_cmds(request, session_url_tag, game_url_tag, game_type):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=game_type
    )
    if game.game_config().management_commands is not None:
        for cmd_name in game.game_config().management_commands:
            management.call_command(
                cmd_name, session=session.url_tag, game=game.url_tag
            )
        return quick_game_admin_render(
            request, session, game, "The management commands have been run."
        )
    return quick_game_admin_render(
        request, session, game, "There are no management commands for this game."
    )
