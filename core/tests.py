from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group

from core.models import Session


class IndexViewTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user_password = "testpassword"
        self.user = User.objects.create_user(
            username="testuser", password=self.user_password
        )
        self.user.is_active = True
        self.user.save()
        group = Group.objects.create(name="TestGroup")
        self.session = Session.objects.create(
            slug_name="your-session-slug",
            name="Your Session Name",
            long_name="Your Session Long Name",
            can_register=True,
            need_registration=True,
            visible=True,
            group=group,
        )
        self.admin_user = User.objects.create_user(
            username="admin_user",
            password="admin_password",
        )
        self.session.admins.add(self.admin_user)

    def test_get_index_view(self):
        # Test GET request to the index view
        response = self.client.get(reverse("core:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/index.html")

    def test_session_finder_form_submission(self):
        # Test POST request with session finder form submission
        form_data = {"session_name": self.session.name, "session_finder": ""}
        response = self.client.post(reverse("core:index"), form_data)
        self.assertRedirects(
            response, reverse("core:index_session", args=(self.session.slug_name,))
        )

    def test_login_form_submission(self):
        # Test POST request with login form submission
        form_data = {
            "login_form": "",
            "username": self.user.username,
            "password": self.user_password,
        }
        response = self.client.post(reverse("core:index"), form_data)
        self.assertEqual(
            response.status_code, 200
        )  # Successful login should stay on the same page

    def test_registration_form_submission(self):
        # Test POST request with registration form submission
        form_data = {
            "registration_form": "",
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "newpassword",
            "password2": "newpassword",
        }
        response = self.client.post(reverse("core:index"), form_data)
        self.assertEqual(
            response.status_code, 200
        )  # Successful registration should stay on the same page

    def test_invalid_form_submission(self):
        # Test POST request with invalid form submission
        form_data = {"invalid_form": ""}  # Invalid form name
        response = self.client.post(reverse("core:index"), form_data)
        self.assertEqual(response.status_code, 404)  # Should raise a 404 error

    def test_inactive_user_login(self):
        # Test login with an inactive user
        form_data = {
            "login_form": "",
            "username": self.user.username,
            "password": self.user_password,
        }
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse("core:index"), form_data)
        self.assertEqual(
            response.status_code, 200
        )  # Stay on the same page but form invalid and error displayed

    def test_user_created_context_variable(self):
        # Test if 'user_created' context variable is set after registration
        form_data = {
            "registration_form": "",
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "newpassword",
            "password2": "newpassword",
        }
        response = self.client.post(reverse("core:index"), form_data)
        self.assertEqual(response.context["user_created"], True)

    def test_user_context_variable(self):
        # Test if 'user' context variable is set after login
        form_data = {
            "login_form": "",
            "username": "testuser",
            "password": "testpassword",
        }
        response = self.client.post(reverse("core:index"), form_data)
        self.assertIsNotNone(response.context["user"])
