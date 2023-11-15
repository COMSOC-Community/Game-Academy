import functools

from django.http import Http404
from django.shortcuts import get_object_or_404

from core.models import Session
from core.authorisations import is_session_admin


def session_admin_decorator(view_func):
    @functools.wraps(view_func)
    def wrapper(request, session_url_tag, *args, **kwargs):
        session = get_object_or_404(Session, url_tag=session_url_tag)
        if is_session_admin(session, request.user):
            return view_func(request, session_url_tag, *args, **kwargs)
        raise Http404("Only session administrators can see this page.")
    return wrapper
