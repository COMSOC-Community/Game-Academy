import functools

from django.http import Http404
from django.shortcuts import get_object_or_404

from core.models import Session
from core.authorisations import is_session_admin, is_session_super_admin


def session_admin_decorator(view_func):
    """Ensures that the user is a session admin before rendering the page"""
    @functools.wraps(view_func)
    def wrapper(request, session_url_tag, *args, **kwargs):
        session = get_object_or_404(Session, url_tag=session_url_tag)
        if is_session_admin(session, request.user):
            return view_func(request, session_url_tag, *args, **kwargs)
        raise Http404("Only administrators of the session can see this page.")

    return wrapper


def session_super_admin_decorator(view_func):
    """Ensures that the user is a session super admin before rendering the page"""
    @functools.wraps(view_func)
    def wrapper(request, session_url_tag, *args, **kwargs):
        session = get_object_or_404(Session, url_tag=session_url_tag)
        if is_session_super_admin(session, request.user):
            return view_func(request, session_url_tag, *args, **kwargs)
        raise Http404("Only super administrators of the session can see this page.")

    return wrapper
