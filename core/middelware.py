from django.contrib.auth.middleware import AuthenticationMiddleware
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, resolve

import core.authorisations
from core.models import Session

SESSION_SCOPE_IGNORED_VIEWS = [
    "core:logout",
    "core:force_player_logout"
]

LOGIN_IGNORED_VIEWS = [
    "core:index",
    "core:logout",
    "core:session_portal",
    "core:force_player_logout",
]

SESSION_VISIBILITY_IGNORED_VIEWS = [
    "core:force_player_logout"
]

SESSION_ROOT_PATH = "/s/"
SESSION_SLUG_POSITION = 2


class EnforceLoginScopeMiddelware(AuthenticationMiddleware):

    @staticmethod
    def _enforce_login_scope(request):
        path = request.path
        resolver = resolve(path)
        view = resolver.view_name
        if view not in LOGIN_IGNORED_VIEWS and not request.user.is_authenticated:
            raise Http404("Middleware block: this view is not accessible to unauthenticated users.")

        accessed_session_slug = None
        # Test for login
        if path.startswith(SESSION_ROOT_PATH) and request.user.is_authenticated:
            accessed_session_slug = path.split("/")[SESSION_SLUG_POSITION]
            session = get_object_or_404(Session, slug_name=accessed_session_slug)
            is_session_admin = core.authorisations.is_session_admin(session, request.user)
            is_session_player = request.user.is_player and request.user.players.first().session == session
            if view not in LOGIN_IGNORED_VIEWS and not is_session_admin and not is_session_player:
                raise Http404("Middleware block: this view is not accessible to this user (not admin, not player).")
            if view not in SESSION_VISIBILITY_IGNORED_VIEWS and not is_session_admin and not session.visible:
                raise Http404("Middleware block: hidden session views are only accessible to admins")

        # Enforce session scope
        if request.user.is_authenticated and request.user.is_player:
            if view in SESSION_SCOPE_IGNORED_VIEWS:
                return
            session = request.user.players.first().session
            if not accessed_session_slug or accessed_session_slug != session.slug_name:
                response = redirect("core:force_player_logout", session.slug_name)
                response[
                    "Location"] += f"?next={path}&prev={reverse('core:session_home', args=(session.slug_name,))}"
                return response

    def process_request(self, request):
        """
        Use process_request instead of defining __call__ directly;
        Django's middleware layer will process_request in a coroutine in __acall__ if it detects an async context.
        Otherwise, it will use __call__.
        https://github.com/django/django/blob/acde91745656a852a15db7611c08cabf93bb735b/django/utils/deprecation.py#L88-L148
        """
        return self._enforce_login_scope(request)
