from django.contrib.auth.middleware import AuthenticationMiddleware
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, resolve

import core.authorisations
from core.constants import FORBIDDEN_SESSION_URL_TAGS
from core.models import Session, Game
from core.games import INSTALLED_GAMES

# Views that do not require authenticated users
OPEN_VIEWS = [
    "core:index",
    "core:logout",
    "core:message",
    "core:session_portal",
    "core:force_player_logout",
    "admin:index",
    "admin:login",
]

# Views outside of session that can be accessed by players
PLAYER_OPEN_VIEWS = ["core:logout", "core:force_player_logout", "core:change_password"]

# Views within a session that can be accessed by anyone (i.e., non-players)
SESSION_OPEN_VIEWS = [
    "core:session_portal",
]

# Views within a session that can be accessed even if session is not visible
HIDDEN_SESSION_OPEN_VIEWS = ["core:force_player_logout"]

try:
    assert set(SESSION_OPEN_VIEWS).issubset(set(OPEN_VIEWS))
except AssertionError:
    raise ValueError("SESSION_OPEN_VIEWS is not a subset of OPEN_VIEWS")

SESSION_URL_TAG_POSITION = 1
GAME_TYPE_URL_TAG_POSITION = 2
GAME_URL_TAG_POSITION = 3


class EnforceLoginScopeMiddleware(AuthenticationMiddleware):
    @staticmethod
    def _enforce_login_scope(request):
        path = request.path
        resolver = resolve(path)
        view = resolver.view_name
        if view not in OPEN_VIEWS and not request.user.is_authenticated:
            raise Http404(
                "Middleware block: this view is not accessible to unauthenticated users."
            )

        accessed_session_url_tag = None
        # Test for login
        if not any(path.startswith("/" + x) for x in FORBIDDEN_SESSION_URL_TAGS):
            split_path = path.split("/")
            accessed_session_url_tag = split_path[SESSION_URL_TAG_POSITION]
            session = get_object_or_404(Session, url_tag=accessed_session_url_tag)
            if core.authorisations.is_session_admin(session, request.user):
                return
            if session.visible:
                if view in SESSION_OPEN_VIEWS:
                    return
                # We know user is authenticated (assert above, and first test)
                if (
                        not request.user.is_player
                        and request.user.players.first().session == session
                ):
                    raise Http404(
                        "Middleware block: this session view is not accessible to this user "
                        "(not admin, not player)."
                    )
            elif view not in HIDDEN_SESSION_OPEN_VIEWS:
                raise Http404(
                    "Middleware block: hidden session views are only accessible to admins"
                )

            # If we are here we know that if the view is hidden, then the user is an admin
            if len(split_path) > GAME_TYPE_URL_TAG_POSITION:
                game_type_url_tag = split_path[GAME_TYPE_URL_TAG_POSITION]
                for game_config in INSTALLED_GAMES:
                    if game_type_url_tag == game_config.url_tag:
                        game = get_object_or_404(
                            Game,
                            session=session,
                            url_tag=split_path[GAME_URL_TAG_POSITION],
                            game_type=game_config.name,
                        )
                        if not game.visible:
                            raise Http404(
                                "Middleware block: this game is not visible and the user "
                                "is not an admin"
                            )

        # Enforce session scope
        if request.user.is_authenticated and request.user.is_player:
            if view in PLAYER_OPEN_VIEWS:
                return
            session = request.user.players.first().session
            if (
                    not accessed_session_url_tag
                    or accessed_session_url_tag != session.url_tag
            ):
                response = redirect("core:force_player_logout", session.url_tag)
                response[
                    "Location"
                ] += f"?next={path}&prev={reverse('core:session_home', args=(session.url_tag,))}"
                return response

    def process_request(self, request):
        return self._enforce_login_scope(request)
