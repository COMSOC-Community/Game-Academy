from django.contrib.auth.middleware import AuthenticationMiddleware
from django.shortcuts import redirect
from django.urls import reverse, resolve

IGNORED_VIEWS = [
    "core:force_player_logout"
]
SESSION_ROOT_PATH = "/s/"
SESSION_SLUG_POSITION = 2


class EnforceSessionScopeMiddelware(AuthenticationMiddleware):
    @staticmethod
    def _enforce_session_scope(request):
        if not request.user.is_authenticated or not request.user.is_player:
            return

        path = request.path
        try:
            resolver = resolve(path)
        except:
            return
        if resolver.view_name in IGNORED_VIEWS:
            return
        session = request.user.players.first().session
        accessed_session_slug = None
        if path.startswith(SESSION_ROOT_PATH):
            accessed_session_slug = path.split("/")[SESSION_SLUG_POSITION]
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
        return self._enforce_session_scope(request)
