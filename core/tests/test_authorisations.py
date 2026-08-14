from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from core.authorisations import (
    can_create_sessions,
    get_session_admin_status,
    is_session_admin,
    is_session_super_admin,
)
from core.models import CustomUser, Session


def make_session(url_tag="testsession"):
    return Session.objects.create(
        url_tag=url_tag, name=url_tag, long_name=url_tag,
    )


def make_user(username, *, is_staff=False, is_player=False):
    return CustomUser.objects.create_user(
        username=username, password="pw", is_staff=is_staff, is_player=is_player,
    )


class CanCreateSessionsTests(TestCase):
    def test_regular_authenticated_user_can_create_sessions(self):
        user = make_user("alice")
        self.assertTrue(can_create_sessions(user))

    def test_player_restricted_user_cannot_create_sessions(self):
        user = make_user("bob", is_player=True)
        self.assertFalse(can_create_sessions(user))

    def test_anonymous_user_cannot_create_sessions(self):
        self.assertFalse(can_create_sessions(AnonymousUser()))


class GetSessionAdminStatusTests(TestCase):
    def setUp(self):
        self.session = make_session()

    def test_anonymous_user_is_neither_admin_nor_super_admin(self):
        with self.assertNumQueries(0):
            is_admin, is_super_admin = get_session_admin_status(
                self.session, AnonymousUser()
            )
        self.assertFalse(is_admin)
        self.assertFalse(is_super_admin)

    def test_staff_user_is_admin_and_super_admin_without_querying_membership(self):
        staff = make_user("staff", is_staff=True)
        with self.assertNumQueries(0):
            is_admin, is_super_admin = get_session_admin_status(self.session, staff)
        self.assertTrue(is_admin)
        self.assertTrue(is_super_admin)

    def test_unrelated_user_is_neither_admin_nor_super_admin(self):
        outsider = make_user("outsider")
        # Two lightweight existence checks: super_admins, then admins.
        with self.assertNumQueries(2):
            is_admin, is_super_admin = get_session_admin_status(
                self.session, outsider
            )
        self.assertFalse(is_admin)
        self.assertFalse(is_super_admin)

    def test_regular_admin_is_admin_but_not_super_admin(self):
        admin = make_user("admin")
        self.session.admins.add(admin)
        with self.assertNumQueries(2):
            is_admin, is_super_admin = get_session_admin_status(self.session, admin)
        self.assertTrue(is_admin)
        self.assertFalse(is_super_admin)

    def test_super_admin_is_admin_and_super_admin(self):
        super_admin = make_user("superadmin")
        self.session.super_admins.add(super_admin)
        # The admins check is short-circuited once the super_admins check succeeds.
        with self.assertNumQueries(1):
            is_admin, is_super_admin = get_session_admin_status(
                self.session, super_admin
            )
        self.assertTrue(is_admin)
        self.assertTrue(is_super_admin)

    def test_user_who_is_both_admin_and_super_admin_is_reported_as_super_admin(self):
        user = make_user("both")
        self.session.admins.add(user)
        self.session.super_admins.add(user)
        is_admin, is_super_admin = get_session_admin_status(self.session, user)
        self.assertTrue(is_admin)
        self.assertTrue(is_super_admin)

    def test_status_is_scoped_to_the_given_session(self):
        other_session = make_session("othersession")
        admin = make_user("scopedadmin")
        self.session.admins.add(admin)
        is_admin, is_super_admin = get_session_admin_status(other_session, admin)
        self.assertFalse(is_admin)
        self.assertFalse(is_super_admin)


class IsSessionAdminTests(TestCase):
    def setUp(self):
        self.session = make_session()

    def test_true_for_staff(self):
        self.assertTrue(is_session_admin(self.session, make_user("staff", is_staff=True)))

    def test_true_for_admin(self):
        admin = make_user("admin")
        self.session.admins.add(admin)
        self.assertTrue(is_session_admin(self.session, admin))

    def test_true_for_super_admin(self):
        super_admin = make_user("superadmin")
        self.session.super_admins.add(super_admin)
        self.assertTrue(is_session_admin(self.session, super_admin))

    def test_false_for_unrelated_user(self):
        self.assertFalse(is_session_admin(self.session, make_user("outsider")))

    def test_false_for_anonymous_user(self):
        self.assertFalse(is_session_admin(self.session, AnonymousUser()))


class IsSessionSuperAdminTests(TestCase):
    def setUp(self):
        self.session = make_session()

    def test_true_for_staff(self):
        self.assertTrue(
            is_session_super_admin(self.session, make_user("staff", is_staff=True))
        )

    def test_true_for_super_admin(self):
        super_admin = make_user("superadmin")
        self.session.super_admins.add(super_admin)
        self.assertTrue(is_session_super_admin(self.session, super_admin))

    def test_false_for_regular_admin(self):
        admin = make_user("admin")
        self.session.admins.add(admin)
        self.assertFalse(is_session_super_admin(self.session, admin))

    def test_false_for_unrelated_user(self):
        self.assertFalse(is_session_super_admin(self.session, make_user("outsider")))

    def test_false_for_anonymous_user(self):
        self.assertFalse(is_session_super_admin(self.session, AnonymousUser()))
