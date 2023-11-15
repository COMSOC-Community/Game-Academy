from django.contrib.auth.middleware import AuthenticationMiddleware
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, resolve

import core.authorisations
from core.models import Session

# Views that do not require authenticated users
OPEN_VIEWS = [
    "core:index",
    "core:logout",
    "core:session_portal",
    "core:force_player_logout",
]

# Views outside of session that can be accessed by players
PLAYER_OPEN_VIEWS = [
    "core:logout",
    "core:force_player_logout"
]

# Views within a session that can be accessed by anyone (i.e., non-players)
SESSION_OPEN_VIEWS = [
    "core:session_portal",
]

# Views within a session that can be accessed even if session is not visible
HIDDEN_SESSION_OPEN_VIEWS = [
    "core:force_player_logout"
]

try:
    assert set(SESSION_OPEN_VIEWS).issubset(set(OPEN_VIEWS))
except AssertionError:
    raise ValueError("SESSION_OPEN_VIEWS is not a subset of OPEN_VIEWS")

SESSION_ROOT_PATH = "/s/"
SESSION_SLUG_POSITION = 2


class EnforceLoginScopeMiddleware(AuthenticationMiddleware):

    @staticmethod
    def _enforce_login_scope(request):
        path = request.path
        resolver = resolve(path)
        view = resolver.view_name
        if view not in OPEN_VIEWS and not request.user.is_authenticated:
            raise Http404("Middleware block: this view is not accessible to unauthenticated users.")

        accessed_session_url_tag = None
        # Test for login
        if path.startswith(SESSION_ROOT_PATH):
            accessed_session_url_tag = path.split("/")[SESSION_SLUG_POSITION]
            session = get_object_or_404(Session, url_tag=accessed_session_url_tag)
            if core.authorisations.is_session_admin(session, request.user):
                return
            if session.visible:
                if view in SESSION_OPEN_VIEWS:
                    return
                # We know user is authenticated (assert above, and first test)
                if not request.user.is_player and request.user.players.first().session == session:
                    raise Http404("Middleware block: this session view is not accessible to this user "
                                  "(not admin, not player).")
            elif view not in HIDDEN_SESSION_OPEN_VIEWS:
                raise Http404("Middleware block: hidden session views are only accessible to admins")

        # Enforce session scope
        if request.user.is_authenticated and request.user.is_player:
            if view in PLAYER_OPEN_VIEWS:
                return
            session = request.user.players.first().session
            if not accessed_session_url_tag or accessed_session_url_tag != session.url_tag:
                response = redirect("core:force_player_logout", session.url_tag)
                response[
                    "Location"] += f"?next={path}&prev={reverse('core:session_home', args=(session.url_tag,))}"
                return response

    def process_request(self, request):
        """
        Use process_request instead of defining __call__ directly;
        Django's middleware layer will process_request in a coroutine in __acall__ if it detects an async context.
        Otherwise, it will use __call__.
        https://github.com/django/django/blob/acde91745656a852a15db7611c08cabf93bb735b/django/utils/deprecation.py#L88-L148
        """
        return self._enforce_login_scope(request)
