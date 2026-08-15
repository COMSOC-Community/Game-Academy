from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import TestCase, RequestFactory
from django.urls import reverse

from core.views import error_400_view, error_403_view, error_404_view, error_500_view


class StaticPageViewTests(TestCase):
    def test_about_page_renders(self):
        response = self.client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)

    def test_faq_page_renders(self):
        response = self.client.get(reverse("core:faq"))
        self.assertEqual(response.status_code, 200)

    def test_terms_and_conditions_page_renders(self):
        response = self.client.get(reverse("core:terms_and_conditions"))
        self.assertEqual(response.status_code, 200)

    def test_privacy_policy_page_renders(self):
        response = self.client.get(reverse("core:privacy_policy"))
        self.assertEqual(response.status_code, 200)

    def test_cookie_policy_page_renders(self):
        response = self.client.get(reverse("core:cookie_policy"))
        self.assertEqual(response.status_code, 200)


class ErrorViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def build_request(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        request.session = self.client.session
        setattr(request, "_messages", FallbackStorage(request))
        return request

    def test_error_400_view_renders_with_correct_status(self):
        response = error_400_view(self.build_request(), Exception("boom"))
        self.assertEqual(response.status_code, 400)

    def test_error_403_view_renders_with_correct_status(self):
        response = error_403_view(self.build_request(), Exception("boom"))
        self.assertEqual(response.status_code, 403)

    def test_error_404_view_renders_with_correct_status(self):
        response = error_404_view(self.build_request(), Exception("boom"))
        self.assertEqual(response.status_code, 404)

    def test_error_500_view_renders_with_correct_status(self):
        response = error_500_view(self.build_request())
        self.assertEqual(response.status_code, 500)
