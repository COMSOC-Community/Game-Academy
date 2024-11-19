import io
import logging
import os
import tempfile
import zipfile
from io import StringIO

from django.conf import settings
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.core import management
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db.models import Max
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from gameserver.local_settings import MAX_NUM_RANDOM_PER_SESSION
from .authorisations import (
    can_create_sessions,
    is_session_admin,
    is_session_super_admin,
)
from .constants import guest_password, TEAM_USER_USERNAME, team_player_name
from .decorators import session_admin_decorator
from .exportdata import team_to_csv, player_to_csv, games_to_csv, session_to_csv
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
    ImportCSVFileForm,
    RandomPlayersForm,
    RandomAnswersForm, JoinPrivateTeamForm, JoinPublicTeamForm, UpdatePasswordForm,
    DeleteAccountForm,
)
from .models import CustomUser, Session, Player, Game, Team
from .utils import sanitise_filename


# ==================
#    ERROR RENDER
# ==================


def error_render(request, template, status):
    """Render function used for all errors"""
    response = render(request, template, locals())
    response.status_code = status
    return response


def error_400_view(request, exception):
    """Render error 400"""
    return error_render(request, "400.html", 400)


def error_403_view(request, exception):
    """Render error 403"""
    return error_render(request, "403.html", 403)


def error_404_view(request, exception):
    """Render error 404"""
    return error_render(request, "404.html", 404)


def error_500_view(request):
    """Render error 500"""
    return error_render(request, "500.html", 500)


# ===================
#    SPECIAL VIEWS
# ===================


def validate_next_url(request, next_url):
    """Check that the url passed in parameter is safe. Use to secure the use of get parameters for
    redirecting URLs."""
    return url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


def force_player_logout(request, session_url_tag):
    """View that forces a player user, i.e., someone restricted to their session to log out before
    continuing if they are attempting to reach a page that is not part of their session."""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    next_url = request.GET.get("next")
    # If POST, the form has been submitted and the user chose to log out and continue where
    # they wanted to go (coming back is a simple link, not a form).
    if request.method == "POST":
        if "logout_and_continue" in request.POST:
            logout(request)
            # If there is a next URL we redirect there, otherwise we go to the index page
            if "next" in request.GET:
                next_url = request.GET["next"]
                if validate_next_url(request, next_url):
                    return redirect(next_url)
            return redirect("core:index")
        else:
            raise Http404("POST request but unknown form type")

    # The URL to stay within the session can be passed as a GET "prev" argument, we default
    # to the home page of the session if the argument is not there.
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
        {"session": session, "url_back": url_back, "next_url": next_url},
    )


def message(request):
    """View to display a message and redirect somewhere afterwards"""
    context = {
        "next_url": reverse("core:index"),
        "message": request.session.pop(
            "_message_view_message", "This is the default message"
        ),
    }
    # If there is no next URL or it's not valid, we default to the home page of the site
    next_url = request.session.pop("_message_view_next_url", None)
    if next_url:
        if not validate_next_url(request, next_url):
            next_url = None
    if not next_url:
        next_url = reverse("core:index")
    context["next_url"] = next_url
    return render(request, "core/message.html", context)


def redirect_to_session_main(session):
    """Helper function that redirects to the home page of a session. Used to ensure the correct
    behaviour of the session.game_after_logging parameter."""
    if session.game_after_logging is not None:
        game = session.game_after_logging
        return redirect(
            f"{game.game_config().url_namespace}:{game.initial_view}",
            session_url_tag=game.session.url_tag,
            game_url_tag=game.url_tag,
        )
    return redirect("core:session_home", session_url_tag=session.url_tag)


# ==========================
#    CONTEXT INITIALISERS
# ==========================

# These are functions that inialise contexts for different types of view. It would probably be
# cleaner to use class-based views instead but well...

def base_context_initialiser(request, context=None):
    """Initialise the context for any page. Mainly fills up the information related to the user,
    notably for the side panel.

    If a context is passed as argument, the latter is extended with the relevant information."""
    if context is None:
        context = {}
    context["user_is_authenticated"] = request.user.is_authenticated
    context["show_side_panel"] = context["user_is_authenticated"]
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
    """Initialise the context for a page in a session. Adds the information related to the admin of
    a session and correct display based on the session parameters.

    If a context is passed as argument, the latter is extended with the relevant information."""
    if context is None:
        context = {}
    context["session"] = session
    if request.user.is_authenticated:
        context["user_is_session_admin"] = is_session_admin(session, request.user)
        context["user_is_session_super_admin"] = is_session_super_admin(
            session, request.user
        )
    if not session.show_side_panel and not context.get("user_is_session_admin", False):
        context["show_side_panel"] = False
        context["session_portal_url"] = reverse("core:session_portal", kwargs={"session_url_tag": session.url_tag})
    return context


def game_context_initialiser(request, session, game, answer_model, context=None):
    """Initialise the context for a page of a game in a session. Adds information about the player
    (submitted answer if exists, etc...) together with extra display details.

    If a context is passed as argument, the latter is extended with the relevant information."""
    if context is None:
        context = {}
    context["game"] = game
    # Retrieve the player, the team if the game requires one, and the potential answer submitted
    # by the player
    player = None
    team = None
    answer = None
    try:
        player = Player.objects.get(session=session, user=request.user)
    except Player.DoesNotExist:
        pass
    if player:
        try:
            team = player.teams.get(game=game)
        except Team.DoesNotExist:
            pass
    try:
        if team:
            answer = answer_model.objects.get(game=game, player=team.team_player)
        else:
            answer = answer_model.objects.get(game=game, player=player)
    except (Player.DoesNotExist, answer_model.DoesNotExist):
        pass
    context["player"] = player
    context["team"] = team
    context["answer"] = answer
    # "submitting_player" defines the player used to submit the answer, in case of a team we use the
    # fake player corresponding to the team
    if game.needs_teams:
        context["submitting_player"] = team.team_player if team else None
    else:
        context["submitting_player"] = player

    # Display stuff
    context["game_nav_display_home"] = session.show_game_nav_home
    context["game_nav_display_team"] = game.needs_teams and game.playable and not team
    context["game_nav_display_answer"] = (
        game.playable and not answer and not context["game_nav_display_team"]
    )
    context["game_nav_display_result"] = game.results_visible and session.show_game_nav_home

    # If admin we add extra information: number of registered players/teams and number of answers
    # received
    if context["user_is_session_admin"]:
        num_players = game.session.players.filter(is_team_player=False).count()
        context["num_players"] = num_players
        num_answer_received = answer_model.objects.filter(game=game).count()
        context["num_received_answers"] = num_answer_received
        if game.needs_teams:
            num_teams = game.teams.count()
            context["num_teams"] = num_teams
            if num_teams > 0:
                context["percent_answer_received"] = (
                    100 * num_answer_received / num_teams
                )
            else:
                context["percent_answer_received"] = 0
        else:
            if num_players > 0:
                context["percent_answer_received"] = (
                    100 * num_answer_received / num_players
                )
            else:
                context["percent_answer_received"] = 0

    return context


# ====================
#    GENERAL INDEX
# ====================


def index(request):
    """Index of the website. Displays different forms: sign in, register and join a session."""
    # Initialise the context
    context = base_context_initialiser(request)

    login_form = LoginForm()
    registration_form = UserRegistrationForm()
    session_finder_form = SessionFinderForm()
    # If POST, we go through the different possible forms to check which has been submitted
    if request.method == "POST":
        # Form to find a session by name, if valid we send the user to the session
        if "session_finder" in request.POST:
            session_finder_form = SessionFinderForm(request.POST)
            if session_finder_form.is_valid():
                return redirect(
                    "core:session_portal",
                    session_url_tag=session_finder_form.cleaned_data["session_url_tag"],
                )
        # Log in form, if valid the user is logged in and we stay on the index page
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
        # Registration form, if valid the user is created and we stay on the index page
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


def about(request):
    """View for the about page of the website."""
    context = base_context_initialiser(request)
    return render(request, "core/about.html", context=context)


def faq(request):
    """View for the FAQ page of the website."""
    context = base_context_initialiser(request)
    return render(request, "core/faq.html", context=context)


def terms_and_conditions(request):
    """View for the Terms and Conditions page of the website."""
    context = base_context_initialiser(request)
    return render(request, "core/terms_and_conditions.html", context=context)


def privacy_policy(request):
    """View for the Privacy Policy page of the website."""
    context = base_context_initialiser(request)
    return render(request, "core/privacy_policy.html", context=context)


def cookie_policy(request):
    """View for the Cookie Policy page of the website."""
    context = base_context_initialiser(request)
    return render(request, "core/cookie_policy.html", context=context)


# ================
#    USER VIEWS
# ================


def logout_user(request):
    """View to log out a user and then redirect to the next URL"""
    logout(request)
    next_url = request.GET.get("next")
    if next_url:
        if validate_next_url(request, next_url):
            return redirect(next_url)
    return redirect("core:index")


def user_profile(request, user_id):
    """View to display the details of a user. Offers a form to change the password and """
    user = get_object_or_404(CustomUser, id=user_id)
    if request.user != user:
        raise Http404("This page is not the business of the logged-in user.")

    context = base_context_initialiser(request)

    # Update Password
    update_password_form = UpdatePasswordForm(user=user)
    if request.method == "POST" and "update_password_form" in request.POST:
        update_password_form = UpdatePasswordForm(request.POST, user=user)
        if update_password_form.is_valid():
            # If valid we update the password and the Django session
            request.user.set_password(update_password_form.cleaned_data["new_password1"])
            request.user.save()
            update_session_auth_hash(request, request.user)
            request.session[
                "_message_view_message"
            ] = f"Your password has been changed."
            # Redirect depending on whether the user is session-restricted or not
            if request.user.is_player:
                request.session["_message_view_next_url"] = reverse("core:session_home", kwargs={
                    "session_url_tag": user.players.first().session.url_tag
                })
            else:
                request.session["_message_view_next_url"] = reverse(
                    "core:user_profile",
                    kwargs={"user_id": user.id},
                )
            return redirect("core:message")
    context["update_password_form"] = update_password_form

    # Delete Account
    delete_account_form = DeleteAccountForm(user=request.user)
    if request.method == "POST" and "delete_account_form" in request.POST:
        delete_account_form = DeleteAccountForm(request.POST, user=request.user)
        if delete_account_form.is_valid():
            request.session[
                "_message_view_message"
            ] = f"Your account {user.username} has been deleted. Have fun under new skies!"
            # Redirect depending on whether the user is session-restricted or not
            if request.user.is_player:
                request.session["_message_view_next_url"] = reverse("core:session_portal", kwargs={
                    "session_url_tag": user.players.first().session.url_tag
                })
            else:
                request.session["_message_view_next_url"] = reverse("core:index")
            user.delete()
            return redirect("core:message")
    context["delete_account_form"] = delete_account_form

    return render(request, "core/user_profile.html", context)


# ===========================
#    GENERAL SESSION VIEWS
# ===========================


def create_session(request):
    """View to create a session. A simple form."""
    user_can_create_session = can_create_sessions(request.user)
    if not user_can_create_session:
        raise Http404("This user cannot create sessions.")

    context = base_context_initialiser(request)
    # Ensures that the user has not yet created too many sessions
    if len(context["user_administrated_sessions"]) >= settings.MAX_NUM_SESSION_PER_USER:
        context["MAX_NUM_SESSION_PER_USER"] = settings.MAX_NUM_SESSION_PER_USER
        context["max_num_session_reached"] = True
    else:
        # If creating a session is possible, we deal with the form.
        create_session_form = CreateSessionForm()
        if request.method == "POST":
            if "create_session_form" in request.POST:
                create_session_form = CreateSessionForm(request.POST)
                if create_session_form.is_valid():
                    session_obj = Session.objects.create(
                        url_tag=create_session_form.cleaned_data["url_tag"],
                        name=create_session_form.cleaned_data["name"],
                        long_name=create_session_form.cleaned_data["long_name"],
                        show_guest_login=create_session_form.cleaned_data[
                            "show_guest_login"
                        ],
                        show_user_login=create_session_form.cleaned_data["show_user_login"],
                        show_create_account=create_session_form.cleaned_data[
                            "show_create_account"
                        ],
                        visible=create_session_form.cleaned_data["visible"],
                    )
                    # The creator of the session is by default a super-admin of the session (and
                    # thus also an admin)
                    session_obj.admins.add(request.user)
                    session_obj.super_admins.add(request.user)
                    create_session_form = CreateSessionForm()
                    context["created_session"] = session_obj
            else:
                raise Http404("POST request received but form type unknown.")
        context["create_session_form"] = create_session_form
    return render(request, "core/create_session.html", context)


def session_portal(request, session_url_tag):
    """View for the portal of a session, i.e., the entry page to a session. Offers log in and sign
    up forms."""
    session = get_object_or_404(Session, url_tag=session_url_tag)

    context = base_context_initialiser(request)
    context["session"] = session

    authenticated_user = request.user.is_authenticated
    is_user_admin = is_session_admin(session, request.user)
    # If the user is a session admin, then log in is not necessary and we already display the
    # session context. Otherwise, this is just a basic page.
    if is_user_admin:
        session_context_initialiser(request, session, context)

    if request.method == "POST":
        if "registration_form" in request.POST and session.show_create_account:
            registration_form = PlayerRegistrationForm(
                request.POST,
                session=session,
                passwords_display=not authenticated_user,
            )
            if registration_form.is_valid():
                # If user is not already authenticated, we need to create one and then to
                # attach the player profile to it
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
                        return redirect_to_session_main(session)
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
        elif "login_form" in request.POST and session.show_user_login:
            login_form = PlayerLoginForm(request.POST, session=session)
            if login_form.is_valid():
                user = authenticate(
                    username=login_form.cleaned_data["user"].username,
                    password=login_form.cleaned_data["password"],
                )
                if user:
                    login(request, user)
                    if "player" in login_form.cleaned_data:
                        # If we are loging in a player, we redirected to home. For regular users,
                        # the "player" of the login form is set in the clean method so that
                        # it is set if the user has a player profile
                        return redirect_to_session_main(session)
                    # If not, we are loging in a user, thus we stay here because they don't have a
                    # profile yet
                    return redirect(
                        "core:session_portal", session_url_tag=session.url_tag
                    )
                # Something weird happened: form is valid but authenticate fails
                context["general_login_error"] = True
            else:
                context["login_form"] = login_form

        elif "guest_form" in request.POST and session.show_guest_login:
            guest_form = SessionGuestRegistration(request.POST, session=session)
            if guest_form.is_valid():
                # We create a user and a player for the guest
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
                    )
                    user = authenticate(
                        username=user.username, password=guest_password(user.username)
                    )
                    if user:
                        login(request, user)
                        return redirect_to_session_main(session)
                    # Something weird happened: form is valid but authenticate fails
                    context["general_login_error"] = True
                except Exception as e:
                    # If an exception occurred, we clean up the mess
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
    if session.show_create_account and "registration_form" not in context:
        context["registration_form"] = PlayerRegistrationForm(
            session=session, passwords_display=not authenticated_user
        )
    if session.show_guest_login and "guest_form" not in context:
        context["guest_form"] = SessionGuestRegistration(session=session)
    if authenticated_user:
        player_profile = Player.objects.filter(session=session, user=request.user)
        if player_profile.exists():
            player_profile = player_profile.first()
            context["player_profile"] = player_profile
    elif session.show_user_login and "login_form" not in context:
        context["login_form"] = PlayerLoginForm(session=session)
    return render(request, "core/session_portal.html", context)


def session_home(request, session_url_tag):
    """View for the home of a session, display all the games available"""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    games = Game.objects.filter(session=session, visible=True)

    # Initialise the context for a session page
    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)

    context["games"] = games

    # If admin, we add the games that are not visible to the players
    if is_session_admin(session, request.user):
        context["invisible_games"] = Game.objects.filter(session=session, visible=False)

    return render(request, "core/session_home.html", context)


# =========================
#    ADMIN SESSION VIEWS
# =========================


@session_admin_decorator
def session_admin(request, session_url_tag):
    """View for the modifying the details of the session. Offers forms to modify the settings of the
    session and to delete it. Session export functionality are also displayed there."""
    session = get_object_or_404(Session, url_tag=session_url_tag)

    # We initialise the context for a session page
    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)

    # Modify session form. We use the CreateSessionForm by passing a session to it to use it as
    # a modify form instead
    modify_session_form = CreateSessionForm(session=session)
    delete_session_form = DeleteSessionForm(user=request.user)
    if request.method == "POST":
        if "modify_session_form" in request.POST:
            modify_session_form = CreateSessionForm(request.POST, session=session)
            if modify_session_form.is_valid():
                session.name = modify_session_form.cleaned_data["name"]
                session.long_name = modify_session_form.cleaned_data["long_name"]
                session.show_user_login = modify_session_form.cleaned_data[
                    "show_user_login"
                ]
                session.show_guest_login = modify_session_form.cleaned_data[
                    "show_guest_login"
                ]
                session.show_create_account = modify_session_form.cleaned_data[
                    "show_create_account"
                ]
                session.visible = modify_session_form.cleaned_data["visible"]
                if "game_after_logging" in modify_session_form.cleaned_data:
                    session.game_after_logging = modify_session_form.cleaned_data[
                        "game_after_logging"
                    ]
                if "show_side_panel" in modify_session_form.cleaned_data:
                    session.show_side_panel = modify_session_form.cleaned_data[
                        "show_side_panel"
                    ]
                if "show_game_nav_home" in modify_session_form.cleaned_data:
                    session.show_game_nav_home = modify_session_form.cleaned_data[
                        "show_game_nav_home"
                    ]
                if "show_game_nav_result" in modify_session_form.cleaned_data:
                    session.show_game_nav_result = modify_session_form.cleaned_data[
                        "show_game_nav_result"
                    ]
                session.save()

                context["session_modified"] = True
                modify_session_form = CreateSessionForm(session=session)
        elif "delete_session_form" in request.POST:
            delete_session_form = DeleteSessionForm(request.POST, user=request.user)
            if delete_session_form.is_valid():
                # Show a confirm message once the session has been deleted
                request.session[
                    "_message_view_message"
                ] = f"The session {session.name} has been deleted."
                request.session["_message_view_next_url"] = reverse("core:index")
                session.delete()
                return redirect("core:message")
        else:
            raise Http404("POST request but form type unknown.")

    context["modify_session_form"] = modify_session_form
    context["delete_session_form"] = delete_session_form
    return render(request, "core/session_admin.html", context)


@session_admin_decorator
def session_admin_export(request, session_url_tag):
    """Returns a CSV response with the session's settings."""
    session = get_object_or_404(Session, url_tag=session_url_tag)

    # Initialise the response as a CSV file
    response = HttpResponse(content_type="text/csv")
    filename = sanitise_filename(f"{session.name}_parameters")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

    # Write the csv file in the request
    session_to_csv(response, session)

    return response


@session_admin_decorator
def session_admin_export_full(request, session_url_tag):
    """Returns a ZIP response with all the CSV files from the element of the session."""
    session = get_object_or_404(Session, url_tag=session_url_tag)

    # We create the zip file on the fly
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Parameters of the session
        session_buffer = io.StringIO()
        session_to_csv(session_buffer, session)
        zip_file.writestr(
            sanitise_filename(f"{session.name}_parameters") + ".csv",
            session_buffer.getvalue(),
        )

        # Players of the session
        player_buffer = io.StringIO()
        player_to_csv(player_buffer, session)
        zip_file.writestr(
            sanitise_filename(f"{session.name}_players") + ".csv",
            player_buffer.getvalue(),
        )

        # Games of the session
        games_buffer = io.StringIO()
        games_to_csv(games_buffer, session)
        zip_file.writestr(
            sanitise_filename(f"{session.name}_games") + ".csv", games_buffer.getvalue()
        )

        # For each game, the export function is called if it is set up
        for game in Game.objects.filter(session=session):
            # Game settings export
            settings_export_function = game.game_config().settings_to_csv_func
            if settings_export_function is not None:
                settings_buffer = io.StringIO()
                settings_export_function(settings_buffer, game)
                zip_file.writestr(
                    sanitise_filename(f"{session.name}_{game.name}_settings") + ".csv",
                    settings_buffer.getvalue(),
                )

            # Answers export
            answers_export_function = game.game_config().answer_to_csv_func
            if answers_export_function is not None:
                answers_buffer = io.StringIO()
                answers_export_function(answers_buffer, game)
                zip_file.writestr(
                    sanitise_filename(f"{session.name}_{game.name}_answers") + ".csv",
                    answers_buffer.getvalue(),
                )

            # Team export
            if game.needs_teams:
                teams_buffer = io.StringIO()
                team_to_csv(teams_buffer, game)
                zip_file.writestr(
                    sanitise_filename(f"{session.name}_{game.name}_teams") + ".csv",
                    teams_buffer.getvalue(),
                )

    # We return the zip file as the response
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type="application/zip")
    filename = sanitise_filename({session.name})
    response["Content-Disposition"] = f'attachment; filename="{filename}.zip"'

    return response


@session_admin_decorator
def session_admin_games(request, session_url_tag):
    """View to admin the games of the session. Offers the form to add new games and lists the game
    already in the session."""
    session = get_object_or_404(Session, url_tag=session_url_tag)

    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)

    # Create game form
    # We only offer the form if the limit of games per session has not yet been reached
    if len(session.games.all()) >= settings.MAX_NUM_GAMES_PER_SESSION:
        context["max_num_games_reached"] = True
        context["MAX_NUM_GAMES_PER_SESSION"] = settings.MAX_NUM_GAMES_PER_SESSION
    else:
        create_game_form = CreateGameForm(session=session)
        if request.method == "POST" and "create_game_form" in request.POST:
            create_game_form = CreateGameForm(request.POST, session=session)
            if create_game_form.is_valid():
                games = session.games
                if games.exists():
                    # If there already are games, we give the new game the highest priority
                    ordering_priority = (
                        session.games.aggregate(Max("ordering_priority"))[
                            "ordering_priority__max"
                        ]
                        + 1
                    )
                else:
                    ordering_priority = 0
                new_game = Game.objects.create(
                    game_type=create_game_form.cleaned_data["game_type"],
                    name=create_game_form.cleaned_data["name"],
                    url_tag=create_game_form.cleaned_data["url_tag"],
                    session=session,
                    playable=create_game_form.cleaned_data["playable"],
                    visible=create_game_form.cleaned_data["visible"],
                    results_visible=create_game_form.cleaned_data["results_visible"],
                    needs_teams=create_game_form.cleaned_data["needs_teams"],
                    description=create_game_form.cleaned_data["description"],
                    ordering_priority=ordering_priority,
                )
                # If the "home_view" for the game app is not configured, we try to find an "index"
                # view, we eventually default to the first available URL if nothing works
                if new_game.game_config().home_view is not None:
                    home_view = new_game.game_config().home_view
                else:
                    all_url_names = new_game.all_url_names()
                    if "index" in all_url_names:
                        home_view = "index"
                    else:
                        home_view = all_url_names[0]
                new_game.initial_view = home_view
                # By default, after submitting we get back to the home_view
                new_game.view_after_submit = home_view

                # We set the illustration of the new game, by selecting the next illustration
                # available (in a cycle)
                game_config = new_game.game_config()
                num_games_of_type = (
                    session.games.filter(game_type=new_game.game_type).count() - 1
                )
                all_illustrations = game_config.illustration_paths
                new_game.illustration_path = all_illustrations[
                    num_games_of_type % len(all_illustrations)
                ]
                new_game.save()

                # If there is a setting model, we need to create it as well.
                if game_config.setting_model is not None:
                    try:
                        game_config.setting_model.objects.create(game=new_game)
                    except Exception as e:
                        raise RuntimeError(
                            "Something went wrong when creating the instance of the setting model "
                            "for the game. Are you sure that your setting model only requires a "
                            "'game' parameter and no additional one?"
                        ) from e

                create_game_form = CreateGameForm(session=session)
                context["new_game"] = new_game

        # In case we created a new game, we check again for the max number of games per session
        if "new_game" in context and len(session.games.all()) == settings.MAX_NUM_GAMES_PER_SESSION - 1:
            context["max_num_games_reached"] = True
            context["MAX_NUM_GAMES_PER_SESSION"] = settings.MAX_NUM_GAMES_PER_SESSION
        else:
            context["create_game_form"] = create_game_form

    # Delete game form
    if request.method == "POST" and "delete_game_form" in request.POST:
        deleted_game_id = request.POST["remove_game_id"]
        deleted_game = Game.objects.get(id=deleted_game_id)
        context["deleted_game_name"] = deleted_game.name
        deleted_game.delete()

    # Delete all games form
    if request.method == "POST" and "delete_all_games_form" in request.POST:
        Game.objects.filter(session=session).delete()
        context["all_games_deleted"] = True

    context["games"] = Game.objects.filter(session=session)
    return render(request, "core/session_admin_games.html", context)


@session_admin_decorator
def session_admin_games_export(request, session_url_tag):
    """View to export the setting of a game in a CSV file"""
    session = get_object_or_404(Session, url_tag=session_url_tag)

    response = HttpResponse(content_type="text/csv")
    filename = sanitise_filename(f"{session.name}_games")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

    games_to_csv(response, session)

    return response


@session_admin_decorator
def session_admin_players(request, session_url_tag):
    """View for the page to admin the players of a session. Displays all the players of the session.
    Offers forms to add new players, to delete some, etc... """
    session = get_object_or_404(Session, url_tag=session_url_tag)

    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)

    # Add player form
    add_player_form = PlayerRegistrationForm(session=session)
    if request.method == "POST" and "add_player_form" in request.POST:
        add_player_form = PlayerRegistrationForm(request.POST, session=session)
        if add_player_form.is_valid():
            # Create the user and the player profile
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
                # If something happens, we delete the user not to leave some mess behind
                user.delete()
                logger = logging.getLogger("Core_SessionPortal")
                logger.exception("An exception occurred while creating a player", e)
                context["player_creation_error"] = True
    context["add_player_form"] = add_player_form

    # Random players form
    num_random_players = Player.objects.filter(session=session, user__is_random_player=True).count()
    # We can only add random players if the limit for random players has not been reached.
    if num_random_players >= MAX_NUM_RANDOM_PER_SESSION:
        context["max_num_random_players_reached"] = True
        context["MAX_NUM_RANDOM_PER_SESSION"] = MAX_NUM_RANDOM_PER_SESSION
        context["num_random_players"] = num_random_players
    else:
        random_players_form = RandomPlayersForm()
        if request.method == "POST" and "random_players_form" in request.POST:
            random_players_form = RandomPlayersForm(request.POST)
            if random_players_form.is_valid():
                num_players = random_players_form.cleaned_data["num_players"]

                # Run the management command and capture its stdout to display the log on the
                # website
                try:
                    out = StringIO()
                    params = {"stdout": out}
                    management.call_command(
                        "generate_random_players",
                        num_players,
                        session=session.url_tag,
                        **params,
                    )
                    context["random_players_log"] = out.getvalue()
                    random_players_form = RandomPlayersForm()
                except Exception as e:
                    context["random_players_error"] = e.__repr__()
                    raise e
        context["random_players_form"] = random_players_form

    # Import player CSV form
    import_player_csv_form = ImportCSVFileForm()
    if request.method == "POST" and "import_player_csv_form" in request.POST:
        import_player_csv_form = ImportCSVFileForm(request.POST, request.FILES)
        if import_player_csv_form.is_valid():
            # We get the file submitted in the form
            uploaded_file = request.FILES["csv_file"]
            file_name = FileSystemStorage(location=tempfile.gettempdir()).save(
                uploaded_file.name, uploaded_file
            )
            # We try running the import command, capturing its stdout to display the log
            try:
                out = StringIO()
                params = {"stdout": out}
                management.call_command(
                    "import_players_csv",
                    os.path.join(tempfile.gettempdir(), file_name),
                    session.url_tag,
                    **params,
                )
                context["import_player_csv_log"] = out.getvalue()
            except Exception as e:
                context["import_player_csv_error"] = e.__repr__()
    context["import_player_csv_form"] = import_player_csv_form

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
        if player.user.is_player:
            player.user.delete()
        player.delete()

    # Delete all players form
    if request.method == "POST" and "delete_all_players_form" in request.POST:
        Player.objects.filter(session=session, user__is_guest_player=False).delete()
        context["all_players_deleted"] = True

    # Delete all randomly generated players form
    if request.method == "POST" and "delete_all_random_players_form" in request.POST:
        Player.objects.filter(session=session, user__is_random_player=True).delete()
        context["all_random_players_deleted"] = True

    # Delete all guests form
    if request.method == "POST" and "delete_all_guests_form" in request.POST:
        Player.objects.filter(session=session, user__is_guest_player=True).delete()
        context["all_guests_deleted"] = True

    if is_session_super_admin(session, request.user):
        # Make (super-)admin form
        make_admin_form = MakeAdminForm(session=session)
        if request.method == "POST" and "make_admin_form" in request.POST:
            make_admin_form = MakeAdminForm(request.POST, session=session)
            if make_admin_form.is_valid():
                user = make_admin_form.cleaned_data["user"]
                session.admins.add(user)
                # If asked for it, we make the user super-admin
                if make_admin_form.cleaned_data["super_admin"]:
                    session.super_admins.add(user)
                make_admin_form = MakeAdminForm(session=session)
                context["new_admin"] = user
        context["make_admin_form"] = make_admin_form

        # Remove admin form
        if request.method == "POST" and "remove_admin_form" in request.POST:
            admin_id = request.POST["remove_admin_id"]
            admin = CustomUser.objects.get(id=admin_id)
            session.super_admins.remove(admin)
            session.admins.remove(admin)
            context["removed_admin"] = admin

    super_admins = session.super_admins.all()
    context["super_admins"] = super_admins
    context["admins"] = session.admins.exclude(id__in=super_admins)
    context["players"] = Player.objects.filter(session=session, user__is_guest_player=False)
    context["guests"] = Player.objects.filter(session=session, user__is_guest_player=True)

    return render(request, "core/session_admin_players.html", context)


@session_admin_decorator
def session_admin_players_export(request, session_url_tag):
    """View to export players of a session in a CSV file."""
    session = get_object_or_404(Session, url_tag=session_url_tag)

    # Prepare the response as a CSV file
    response = HttpResponse(content_type="text/csv")
    filename = sanitise_filename(f"{session.name}_players")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

    # Write the CSV content in the response
    player_to_csv(response, session)

    return response


@session_admin_decorator
def session_admin_player_password(request, session_url_tag, player_user_id):
    """View that allows an admin to change the password of a player of a session. Only
    the password of a user restricted to a session can be changed."""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    player = get_object_or_404(Player, session=session, user__id=player_user_id, user__is_player=True)

    # Initialise context for a session page
    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)
    context["player"] = player

    # Update password form
    # We use PlayerRegistrationForm and pass it a player argument to use it as a modifier form
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


def create_or_join_team(request, session_url_tag, game_url_tag):
    """View to create or join a team. Public teams are all visible and can be joined with a
    simple click. Private teams are joined by searching for their name."""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, needs_teams=True
    )

    if not game.needs_teams:
        raise Http404("This game does not require teams.")

    # Initialise the context as a game context
    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)
    game_context_initialiser(
        request, session, game, game.game_config().answer_model, context
    )
    context["game_nav_display_team"] = False

    if not game.playable and not context["user_is_session_admin"]:
        raise Http404("The game is not playable and the user is not an admin.")

    # If the player is not yet part of a team, we generate the required objects
    player = context["player"]
    if player and context["team"] is None:
        create_team_form = CreateTeamForm(game=game)
        join_public_team_form = JoinPublicTeamForm(game=game)
        join_private_team_form = JoinPrivateTeamForm(game=game)
        if request.method == "POST":
            # Form to create a team
            if "create_team_form" in request.POST:
                create_team_form = CreateTeamForm(request.POST, game=game)
                if create_team_form.is_valid():
                    team_name = create_team_form.cleaned_data["name"]
                    # We create the user that will represent the team
                    team_player_user = CustomUser.objects.get(
                        username=TEAM_USER_USERNAME
                    )
                    team_player = None
                    try:
                        # We create the player that will represent the team
                        team_player = Player.objects.create(
                            user=team_player_user,
                            name=team_player_name(game.name, team_name),
                            session=session,
                            is_team_player=True,
                        )
                    except Exception as e:
                        # If something goes wrong, we clean the mess
                        team_player_user.delete()
                        raise e
                    # Finally, we create the team
                    if team_player:
                        try:
                            new_team = Team.objects.create(
                                name=create_team_form.cleaned_data["name"],
                                is_public=create_team_form.cleaned_data["is_public"],
                                game=game,
                                creator=player,
                                team_player=team_player,
                            )
                            new_team.players.add(player)
                            new_team.save()
                        except Exception as e:
                            # If something goes wrong, we clean the mess
                            team_player_user.delete()
                            raise e
                        context["created_team"] = new_team
            # Form to join public teams
            elif "join_public_team_form" in request.POST:
                join_public_team_form = JoinPublicTeamForm(request.POST, game=game)
                if join_public_team_form.is_valid():
                    joined_team = join_public_team_form.cleaned_data["team"]
                    joined_team.players.add(player)
                    joined_team.save()
                    context["joined_team_name"] = joined_team.name
            # Form to join private teams
            elif "join_private_team_form" in request.POST:
                join_private_team_form = JoinPrivateTeamForm(request.POST, game=game)
                if join_private_team_form.is_valid():
                    joined_team = join_private_team_form.cleaned_data["team"]
                    joined_team.players.add(player)
                    context["joined_team_name"] = joined_team.name
            else:
                raise Http404("Form type unknown...")

        context["create_team_form"] = create_team_form
        context["join_private_team_form"] = join_private_team_form
        # If there are no public team, we disable the public team form
        if join_public_team_form.team_count == 0:
            join_public_team_form = None
        context["join_public_team_form"] = join_public_team_form

    return render(request, "core/team.html", context)


# ======================
#    ADMIN GAME VIEWS
# ======================


@session_admin_decorator
def session_admin_games_settings(request, session_url_tag, game_url_tag):
    """View to change the settings of a game."""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag)

    # Initialise context as a session page
    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)

    context["game"] = game

    # Check if there are answers to display a warning message before modifying the settings
    answer_model = game.game_config().answer_model
    if answer_model:
        context["answers_exist"] = answer_model.objects.filter(game=game).exists()

    # Modify game form
    # We use the CreateGameForm passing it a "game" parameter to use it as a modifier form
    modify_game_form = CreateGameForm(session=session, game=game, prefix=game.url_tag)
    # If the app as configured a setting model and form, we retrieve it
    modify_game_setting_form = None
    if game.game_config().setting_form is not None:
        setting_model = game.game_config().setting_model
        # We try to retrieve the setting object by fetching the right attribute based on the
        # related_query_name. Only works if the setting model does use a "game" field as intended.
        game_setting_obj = None
        try:
            game_setting_obj = getattr(
                game, setting_model._meta.get_field("game").related_query_name()
            )
        except ObjectDoesNotExist:
            pass
        # If we retrieve the setting object, we set up the setting form. This only works if the
        # setting form is a ModelForm
        if game_setting_obj:
            modify_game_setting_form = game.game_config().setting_form(
                instance=game_setting_obj
            )
    if request.method == "POST":
        # Modify game, POST handling
        if "modify_game_form" in request.POST:
            modify_game_form = CreateGameForm(
                request.POST, session=session, game=game, prefix=game.url_tag
            )
            if modify_game_form.is_valid():
                game.name = modify_game_form.cleaned_data["name"]
                game.url_tag = modify_game_form.cleaned_data["url_tag"]
                game.playable = modify_game_form.cleaned_data["playable"]
                game.visible = modify_game_form.cleaned_data["visible"]
                game.results_visible = modify_game_form.cleaned_data["results_visible"]
                game.needs_teams = modify_game_form.cleaned_data["needs_teams"]
                game.description = modify_game_form.cleaned_data["description"]
                game.illustration_path = modify_game_form.cleaned_data[
                    "illustration_path"
                ]
                game.ordering_priority = modify_game_form.cleaned_data[
                    "ordering_priority"
                ]
                game.run_management_after_submit = modify_game_form.cleaned_data[
                    "run_management_after_submit"
                ]
                game.initial_view = modify_game_form.cleaned_data["initial_view"]
                game.view_after_submit = modify_game_form.cleaned_data[
                    "view_after_submit"
                ]
                game.save()

                modify_game_form = CreateGameForm(
                    session=session, game=game, prefix=game.url_tag
                )
                context["game_modified"] = True
        # Modify setting POST handling
        elif "modify_game_setting_form" in request.POST:
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
                context["setting_modified"] = True
    context["modify_game_form"] = modify_game_form
    context["modify_game_setting_form"] = modify_game_setting_form

    context["export_settings_configured"] = game.game_config().settings_to_csv_func is not None

    return render(request, "core/session_admin_games_settings.html", context)


@session_admin_decorator
def session_admin_games_settings_export(request, session_url_tag, game_url_tag):
    """View to export a game's settings into a CSV file"""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag)

    # If not export function is configured, we raise a 404
    export_function = game.game_config().settings_to_csv_func
    if export_function is not None:
        # Preparing the response as a CSV file
        response = HttpResponse(content_type="text/csv")
        filename = sanitise_filename(f"{session.name}_{game.name}_settings")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

        # Write the CSV into the response
        export_function(response, game)

        return response
    raise Http404("This game has no answer export function configured.")


@session_admin_decorator
def session_admin_games_answers(request, session_url_tag, game_url_tag):
    """View to handle the answers to a game: exporting the answers, generating random answers,
    deleting answers etc..."""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag)

    # Initialise the context as a session page
    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)

    context["game"] = game

    # Most of this view is only available if an answer model has been configure in the game app
    answer_model = game.game_config().answer_model
    if answer_model is not None:
        # Form to delete an answer
        if request.method == "POST" and "delete_answer_form" in request.POST:
            deleted_answer_id = request.POST["remove_answer_id"]
            answer_to_delete = answer_model.objects.get(id=deleted_answer_id)
            context["deleted_answer_id"] = deleted_answer_id
            context["deleted_answer_player"] = answer_to_delete.player.display_name()
            answer_to_delete.delete()

        # Form to delete all answers
        if request.method == "POST" and "delete_all_answers_form" in request.POST:
            answer_model.objects.filter(game=game).delete()
            context["all_answers_deleted"] = True

        # Form to delete all randomly generated answers
        if request.method == "POST" and "delete_all_random_answers_form" in request.POST:
            answer_model.objects.filter(game=game, player__user__is_random_player=True).delete()
            Team.objects.filter(game=game, creator__user__is_random_player=True).delete()
            context["all_answers_deleted"] = True

        # Generate random answers
        # Only if a random generator function has been configured in the game app
        if game.game_config().random_answers_func is not None:
            num_random_players = Player.objects.filter(session=session, user__is_random_player=True).count()
            # Only available if there are not too many randomly generated user in the session
            if num_random_players >= MAX_NUM_RANDOM_PER_SESSION:
                context["max_num_random_players_reached"] = True
                context["MAX_NUM_RANDOM_PER_SESSION"] = MAX_NUM_RANDOM_PER_SESSION
                context["num_random_players"] = num_random_players
            else:
                random_answers_form = RandomAnswersForm()
                if request.method == "POST" and "random_answers_form" in request.POST:
                    random_answers_form = RandomAnswersForm(request.POST)
                    if random_answers_form.is_valid():
                        num_answers = random_answers_form.cleaned_data["num_answers"]
                        run_management = random_answers_form.cleaned_data["run_management"]
                        # Run the command to generate the answers, capturing the stdout to show the
                        # log
                        try:
                            out = StringIO()
                            params = {"stdout": out}
                            management.call_command(
                                "generate_random_answers",
                                num_answers,
                                session=session.url_tag,
                                game=game.url_tag,
                                run_management=run_management,
                                **params,
                            )
                            context["random_answers_log"] = out.getvalue()
                            random_answers_form = RandomAnswersForm()
                        except Exception as e:
                            context["random_answers_error"] = e.__repr__()
                            raise e
                context["random_answers_form"] = random_answers_form

        # Fetch the fields to display from the game_config
        answer_model_fields = game.game_config().answer_model_fields
        if answer_model_fields is None:
            # We always omit some fields
            omitted_fields = ("id", "game", "player")
            answer_model_fields = [
                f.name
                for f in answer_model._meta.get_fields()
                if f.name not in omitted_fields
            ]
        context["answer_model_fields"] = answer_model_fields
        context["answers"] = answer_model.objects.filter(game=game)
    else:
        context["no_answer_model"] = True

    context["export_answers_configured"] = game.game_config().answer_to_csv_func is not None

    return render(request, "core/session_admin_games_answers.html", context)


@session_admin_decorator
def session_admin_games_answers_export(request, session_url_tag, game_url_tag):
    """View to export answers of a game"""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag)

    # Only if the export function has been configured in the game_config
    export_function = game.game_config().answer_to_csv_func
    if export_function is not None:
        # Prepare the response as a CSV file
        response = HttpResponse(content_type="text/csv")
        filename = sanitise_filename(f"{session.name}_{game.name}_answers")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

        # Write the CSV content to the response
        export_function(response, game)

        return response
    raise Http404("This game has no answer export function configured.")


@session_admin_decorator
def session_admin_games_teams(request, session_url_tag, game_url_tag):
    """View to admin teams of a game"""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag)

    # Initialise the context as a session page
    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)

    # Delete team form
    if request.method == "POST" and "delete_team_form" in request.POST:
        deleted_team_id = request.POST["remove_team_id"]
        team_to_delete = Team.objects.get(id=deleted_team_id)
        context["deleted_team_id"] = deleted_team_id
        context["deleted_team_name"] = team_to_delete.name
        team_to_delete.delete()

    # Delete all teams form
    if request.method == "POST" and "delete_all_teams_form" in request.POST:
        Team.objects.filter(game=game).delete()
        context["all_teams_deleted"] = True

    context["game"] = game
    context["teams"] = Team.objects.filter(game=game)

    return render(request, "core/session_admin_games_teams.html", context)


@session_admin_decorator
def session_admin_games_teams_export(request, session_url_tag, game_url_tag):
    """View to export teams of a game as a CSV file."""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag)

    # Prepare the response as a CSV file
    response = HttpResponse(content_type="text/csv")
    filename = sanitise_filename(f"{session.name}_{game.name}_teams")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

    # Write the content of the CSV into the file
    team_to_csv(response, game)

    return response


def quick_game_admin_render(request, session, game, info_message):
    """Helper function for the quick-access management button for a game. Displays a message
    and redirect as requested."""
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
def game_visibility_toggle(request, session_url_tag, game_url_tag, game_type):
    """View that toggles the visibility of a game."""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=game_type
    )
    game.visible = not game.visible
    game.save()
    if game.visible:
        info_message = "The game is now visible."
    else:
        info_message = "The game is no longer visible."
    return quick_game_admin_render(request, session, game, info_message)


@session_admin_decorator
def game_play_toggle(request, session_url_tag, game_url_tag, game_type):
    """View that toggles the playability of a game."""
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
    """View that toggles the visibility of the results of a game."""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=game_type
    )
    game.results_visible = not game.results_visible
    game.save()

    if game.results_visible:
        info_message = "Players can now see the global_results."
    else:
        info_message = "Players can no longer see the global_results."
    return quick_game_admin_render(request, session, game, info_message)


@session_admin_decorator
def game_run_management_cmds(request, session_url_tag, game_url_tag, game_type):
    """View to run the management commands of a game."""
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=game_type
    )
    # Fetch the commands from the game_config
    if game.game_config().management_commands is not None:
        # Run each command, one after the other
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
