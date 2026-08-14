from unittest import mock

from django.http import Http404, HttpResponse
from django.test import TestCase, RequestFactory

from core.game_views import GameView, GameIndexView, GameSubmitAnswerView, GameResultsView
from core.tests.helpers import make_session, make_user, make_game, make_player


class _StubSubmitAnswerView(GameSubmitAnswerView):
    """A GameSubmitAnswerView with controllable hooks, used to unit test the generic
    post() dispatch logic in isolation from any specific game's form/model."""

    def __init__(self, *args, validated_result=(True, "form_object"), **kwargs):
        super().__init__(*args, **kwargs)
        self._validated_result = validated_result
        self.valid_calls = []
        self.invalid_calls = []
        self.render_calls = 0

    def post_validated_form(self, request):
        return self._validated_result

    def post_code_if_form_valid(self, request, form_object):
        self.valid_calls.append(form_object)

    def post_code_if_form_invalid(self, request, form_object):
        self.invalid_calls.append(form_object)

    def post_code_render(self, request):
        self.render_calls += 1
        return HttpResponse("rendered")


class GameViewTestsBase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.session = make_session("gvsession", visible=True)
        self.game = make_game(self.session, url_tag="numb", visible=True)
        self.user = make_user("gvuser")
        make_player(self.session, self.user, name="gvuser")

    def build_request(self, method="get", user=None):
        request = getattr(self.factory, method)("/irrelevant/")
        request.user = user if user is not None else self.user
        return request


class GameViewSetupTests(GameViewTestsBase):
    def test_setup_raises_without_session_url_tag(self):
        view = GameView()
        request = self.build_request()
        with self.assertRaises(ValueError):
            view.setup(request, game_url_tag=self.game.url_tag)

    def test_setup_raises_without_game_url_tag(self):
        view = GameView()
        request = self.build_request()
        with self.assertRaises(ValueError):
            view.setup(request, session_url_tag=self.session.url_tag)

    def test_setup_resolves_session_and_game_and_populates_context(self):
        view = GameView()
        request = self.build_request()
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        self.assertEqual(view.session, self.session)
        self.assertEqual(view.game, self.game)
        self.assertEqual(view.context["session"], self.session)
        self.assertEqual(view.context["game"], self.game)

    def test_setup_reuses_cached_session_and_game_from_request(self):
        view = GameView()
        request = self.build_request()
        # Simulate what EnforceLoginScopeMiddleware would have already resolved.
        request.resolved_session = self.session
        request.resolved_game = self.game
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        # Proven by object identity: a fresh DB fetch would return an equal but distinct
        # Python object, not the exact same instance we placed on the request.
        self.assertIs(view.session, request.resolved_session)
        self.assertIs(view.game, request.resolved_game)

    def test_setup_ignores_cached_session_that_does_not_match_requested_url(self):
        other_session = make_session("gvothersession", visible=True)
        view = GameView()
        request = self.build_request()
        request.resolved_session = other_session
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        self.assertEqual(view.session, self.session)
        self.assertNotEqual(view.session, other_session)

    def test_setup_ignores_cached_game_that_does_not_match_requested_url(self):
        other_game = make_game(self.session, url_tag="othr", name="Other", visible=True)
        view = GameView()
        request = self.build_request()
        request.resolved_session = self.session
        request.resolved_game = other_game
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        self.assertEqual(view.game, self.game)
        self.assertNotEqual(view.game, other_game)


class GameIndexViewTests(GameViewTestsBase):
    def test_hides_home_nav_button(self):
        view = GameIndexView()
        request = self.build_request()
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        self.assertFalse(view.context["game_nav_display_home"])


class GameSubmitAnswerViewSetupTests(GameViewTestsBase):
    def test_playable_game_is_reachable_by_non_admin(self):
        view = GameSubmitAnswerView()
        request = self.build_request()
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        self.assertFalse(view.context["game_nav_display_answer"])

    def test_non_playable_game_blocks_non_admin(self):
        self.game.playable = False
        self.game.save()
        view = GameSubmitAnswerView()
        request = self.build_request()
        with self.assertRaises(Http404):
            view.setup(
                request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
            )

    def test_non_playable_game_is_reachable_by_admin(self):
        self.game.playable = False
        self.game.save()
        admin = make_user("gvadmin")
        self.session.admins.add(admin)
        view = GameSubmitAnswerView()
        request = self.build_request(user=admin)
        # Should not raise.
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )


class GameSubmitAnswerViewPostTests(GameViewTestsBase):
    def make_stub(self, validated_result):
        view = _StubSubmitAnswerView(validated_result=validated_result)
        request = self.build_request(method="post")
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        return view, request

    def test_valid_form_calls_valid_hook_and_renders(self):
        view, request = self.make_stub((True, "the_form"))
        response = view.post(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        self.assertEqual(view.valid_calls, ["the_form"])
        self.assertEqual(view.invalid_calls, [])
        self.assertEqual(view.render_calls, 1)
        self.assertEqual(response.content, b"rendered")

    def test_invalid_form_calls_invalid_hook_and_renders(self):
        view, request = self.make_stub((False, "bad_form"))
        view.post(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        self.assertEqual(view.invalid_calls, ["bad_form"])
        self.assertEqual(view.valid_calls, [])
        self.assertEqual(view.render_calls, 1)

    @mock.patch("core.game_views.management.call_command")
    def test_management_commands_run_when_flag_true_and_configured(self, mock_call_command):
        self.game.game_type = "numbersgame"
        self.game.run_management_after_submit = True
        self.game.save()
        view, request = self.make_stub((True, "form"))
        view.post(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        mock_call_command.assert_called_once_with(
            "numbersgame_results", session=self.session.url_tag, game=self.game.url_tag
        )

    @mock.patch("core.game_views.management.call_command")
    def test_management_commands_skipped_when_flag_false(self, mock_call_command):
        self.game.game_type = "numbersgame"
        self.game.run_management_after_submit = False
        self.game.save()
        view, request = self.make_stub((True, "form"))
        view.post(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        mock_call_command.assert_not_called()

    @mock.patch("core.game_views.management.call_command")
    def test_management_commands_skipped_when_form_invalid(self, mock_call_command):
        self.game.game_type = "numbersgame"
        self.game.run_management_after_submit = True
        self.game.save()
        view, request = self.make_stub((False, "bad_form"))
        view.post(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        mock_call_command.assert_not_called()


class GameResultsViewTests(GameViewTestsBase):
    def test_visible_results_are_reachable_by_non_admin(self):
        self.game.results_visible = True
        self.game.save()
        view = GameResultsView()
        request = self.build_request()
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
        self.assertFalse(view.context["game_nav_display_result"])

    def test_hidden_results_block_non_admin(self):
        self.game.results_visible = False
        self.game.save()
        view = GameResultsView()
        request = self.build_request()
        with self.assertRaises(Http404):
            view.setup(
                request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
            )

    def test_hidden_results_are_reachable_by_admin(self):
        self.game.results_visible = False
        self.game.save()
        admin = make_user("resultsadmin")
        self.session.admins.add(admin)
        view = GameResultsView()
        request = self.build_request(user=admin)
        # Should not raise.
        view.setup(
            request, session_url_tag=self.session.url_tag, game_url_tag=self.game.url_tag
        )
