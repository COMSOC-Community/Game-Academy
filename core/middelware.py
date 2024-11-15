"""Middleware that ensures that user cannot access pages they are not allowed to. Enforces
appropriate permissions and also that players (thus not global users) cannot leave their
session without logging out."""
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, resolve

import core.authorisations
from core.constants import FORBIDDEN_SESSION_URL_TAGS
from core.game_config import INSTALLED_GAMES_CHOICES
from core.models import Session, Game

# Views that do not require authenticated users
OPEN_VIEWS = {
    "core:index",
    "core:about",
    "core:faq",
    "core:logout",
    "core:message",
    "core:session_portal",
    "core:force_player_logout",
    "admin:index",
    "admin:login",
}

# Views outside of session that can be accessed by players
PLAYER_OPEN_VIEWS = {"core:logout", "core:force_player_logout", "core:user_profile"}

# Views within a session that can be accessed by anyone (i.e., non-players)
SESSION_OPEN_VIEWS = {
    "core:session_portal",
}

# Views within a session that can be accessed even if session is not visible
HIDDEN_SESSION_OPEN_VIEWS = {
    "core:force_player_logout",
}

try:
    assert SESSION_OPEN_VIEWS.issubset(OPEN_VIEWS)
except AssertionError:
    raise ValueError("SESSION_OPEN_VIEWS is not a subset of OPEN_VIEWS")

SESSION_URL_TAG_POSITION = 0
GAME_TYPE_URL_TAG_POSITION = 1
GAME_URL_TAG_POSITION = 2


class EnforceLoginScopeMiddleware(AuthenticationMiddleware):
    @staticmethod
    def _enforce_login_scope(request):
        path = request.path
        resolver = resolve(path)
        view_name = resolver.view_name
        open_view = view_name in OPEN_VIEWS

        authenticated_user = request.user.is_authenticated
        player_user = request.user.is_player if authenticated_user else None
        player_user_session = None
        if player_user:
            player_user_session = request.user.players.first().session

        # If the view is open, and we don't have to enforce the scope, then return
        if open_view and not player_user:
            return
        # If the view is not open, and the user is not authenticated, block the user
        if not open_view and not authenticated_user:
            raise Http404(
                "Middleware block: this view is not accessible to unauthenticated users."
            )

        split_path = [x for x in path.split("/") if x]

        accessed_session_url_tag = None
        # Enforcing all required login depending on what is asked
        if (
            split_path
            and split_path[SESSION_URL_TAG_POSITION] not in FORBIDDEN_SESSION_URL_TAGS
        ):
            accessed_session_url_tag = split_path[SESSION_URL_TAG_POSITION]
            session = get_object_or_404(Session, url_tag=accessed_session_url_tag)
            # If session admin, all is good, return
            if core.authorisations.is_session_admin(session, request.user):
                return
            # If session is visible, we only let it go through if we have a player for the
            # corresponding session
            if session.visible:
                if view_name in SESSION_OPEN_VIEWS and not player_user:
                    return
                # We know user is authenticated (assert above, and first test), session views are
                # only available to players of the session. If player_user, we let go so that it's
                # caught by the session scope enforcement.
                if not player_user:
                    user_players = request.user.players.all()
                    if not user_players:
                        raise Http404(
                            "Middleware block: this session view is not accessible to this user "
                            "(not admin, not player) who has no player profile.")
                    else:
                        if not user_players.filter(session=session).exists():
                            raise Http404(
                                "Middleware block: this session view is not accessible to this "
                                "user (not admin, not player) who is no player of this session."
                            )
            # If session is NOT visible, only admins can access the page
            elif view_name not in HIDDEN_SESSION_OPEN_VIEWS:
                raise Http404(
                    "Middleware block: hidden session views are only accessible to admins"
                )

            # If we are here we know that if the view is hidden, then the user is an admin (and we
            # would have already returned)
            if len(split_path) > GAME_URL_TAG_POSITION:
                # game_type = split_path[GAME_TYPE_URL_TAG_POSITION]
                game_url_tag = split_path[GAME_URL_TAG_POSITION]
                game = get_object_or_404(Game, session=session, url_tag=game_url_tag)
                if not game.visible:
                    raise Http404(
                        "Middleware block: this game is not visible and the user "
                        "is not an admin"
                    )

        # Enforcing session scope for players
        if player_user:
            if view_name in PLAYER_OPEN_VIEWS:
                return
            if (
                not accessed_session_url_tag
                or accessed_session_url_tag != player_user_session.url_tag
            ):
                response = redirect(
                    "core:force_player_logout", player_user_session.url_tag
                )
                response[
                    "Location"
                ] += f"?next={path}&prev={reverse('core:session_home', args=(player_user_session.url_tag,))}"
                return response

    def process_request(self, request):
        return self._enforce_login_scope(request)
