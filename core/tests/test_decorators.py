from django.http import Http404, HttpResponse
from django.test import TestCase, RequestFactory

from core.decorators import session_admin_decorator, session_super_admin_decorator
from core.tests.helpers import make_session, make_user


def dummy_view(request, session_url_tag, *args, **kwargs):
    """Records that it was called and echoes back what it received."""
    dummy_view.called_with = (session_url_tag, args, kwargs)
    return HttpResponse("view was called")


class SessionAdminDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.session = make_session("decoratorsession")
        dummy_view.called_with = None

    def call(self, view, user, *args, **kwargs):
        request = self.factory.get("/irrelevant/")
        request.user = user
        return view(request, self.session.url_tag, *args, **kwargs)

    def test_admin_reaches_the_view(self):
        admin = make_user("decoratoradmin")
        self.session.admins.add(admin)
        wrapped = session_admin_decorator(dummy_view)
        response = self.call(wrapped, admin)
        self.assertEqual(response.content, b"view was called")
        self.assertEqual(dummy_view.called_with, (self.session.url_tag, (), {}))

    def test_super_admin_also_reaches_the_view(self):
        super_admin = make_user("decoratorsuperadmin")
        self.session.super_admins.add(super_admin)
        wrapped = session_admin_decorator(dummy_view)
        self.call(wrapped, super_admin)
        self.assertIsNotNone(dummy_view.called_with)

    def test_staff_user_bypasses_without_explicit_membership(self):
        staff = make_user("decoratorstaff", is_staff=True)
        wrapped = session_admin_decorator(dummy_view)
        self.call(wrapped, staff)
        self.assertIsNotNone(dummy_view.called_with)

    def test_non_admin_is_blocked_and_view_not_called(self):
        outsider = make_user("decoratoroutsider")
        wrapped = session_admin_decorator(dummy_view)
        with self.assertRaises(Http404):
            self.call(wrapped, outsider)
        self.assertIsNone(dummy_view.called_with)

    def test_unknown_session_url_tag_is_404(self):
        admin = make_user("decoratoradmin2")
        wrapped = session_admin_decorator(dummy_view)
        request = self.factory.get("/irrelevant/")
        request.user = admin
        with self.assertRaises(Http404):
            wrapped(request, "no-such-session-tag")

    def test_extra_positional_and_keyword_args_are_passed_through(self):
        admin = make_user("decoratoradmin3")
        self.session.admins.add(admin)
        wrapped = session_admin_decorator(dummy_view)
        self.call(wrapped, admin, "extra_arg", game_url_tag="numb")
        self.assertEqual(
            dummy_view.called_with,
            (self.session.url_tag, ("extra_arg",), {"game_url_tag": "numb"}),
        )

    def test_wraps_preserves_view_metadata(self):
        wrapped = session_admin_decorator(dummy_view)
        self.assertEqual(wrapped.__name__, "dummy_view")
        self.assertEqual(wrapped.__doc__, dummy_view.__doc__)


class SessionSuperAdminDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.session = make_session("supdecoratorsession")
        dummy_view.called_with = None

    def call(self, view, user):
        request = self.factory.get("/irrelevant/")
        request.user = user
        return view(request, self.session.url_tag)

    def test_super_admin_reaches_the_view(self):
        super_admin = make_user("supdecoratorsuperadmin")
        self.session.super_admins.add(super_admin)
        wrapped = session_super_admin_decorator(dummy_view)
        self.call(wrapped, super_admin)
        self.assertIsNotNone(dummy_view.called_with)

    def test_regular_admin_is_blocked(self):
        admin = make_user("supdecoratorregularadmin")
        self.session.admins.add(admin)
        wrapped = session_super_admin_decorator(dummy_view)
        with self.assertRaises(Http404):
            self.call(wrapped, admin)
        self.assertIsNone(dummy_view.called_with)

    def test_non_admin_is_blocked(self):
        outsider = make_user("supdecoratoroutsider")
        wrapped = session_super_admin_decorator(dummy_view)
        with self.assertRaises(Http404):
            self.call(wrapped, outsider)

    def test_staff_user_bypasses_without_explicit_membership(self):
        staff = make_user("supdecoratorstaff", is_staff=True)
        wrapped = session_super_admin_decorator(dummy_view)
        self.call(wrapped, staff)
        self.assertIsNotNone(dummy_view.called_with)

    def test_unknown_session_url_tag_is_404(self):
        super_admin = make_user("supdecoratorsuperadmin2")
        wrapped = session_super_admin_decorator(dummy_view)
        request = self.factory.get("/irrelevant/")
        request.user = super_admin
        with self.assertRaises(Http404):
            wrapped(request, "no-such-session-tag")
