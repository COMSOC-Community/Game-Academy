"""
Collections of view used in the game apps to simply the workflow. Their use is not mandatory but
helps.
"""
from django.core import management
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views import View

from core.models import Session, Game
from core.views import (
    base_context_initialiser,
    session_context_initialiser,
    game_context_initialiser,
)


class GameView(View):
    """Standard view for a game. Sets up the view with the session and the game, together with
    the base context."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = None
        self.game = None
        self.session = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        # Retrieve the session
        session_url_tag = kwargs.get("session_url_tag", None)
        if session_url_tag is None:
            raise ValueError(
                "The game view did not receive a session_url_tag parameter, that is weird..."
            )
        # Retrieve the game
        game_url_tag = kwargs.get("game_url_tag", None)
        if game_url_tag is None:
            raise ValueError(
                "The game view did not receive a game_url_tag parameter, that is weird..."
            )
        session = get_object_or_404(Session, url_tag=session_url_tag)
        game = get_object_or_404(Game, session=session, url_tag=game_url_tag)

        # Initialise the context
        context = base_context_initialiser(request)
        session_context_initialiser(request, session, context)
        game_context_initialiser(
            request, session, game, game.game_config().answer_model, context
        )
        self.session = session
        self.game = game
        self.context = context


class GameIndexView(GameView):
    """View for the index page of a game. Does not do much."""
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context["game_nav_display_home"] = False


class GameSubmitAnswerView(GameView):
    """View for submitted answer to a game. The idea is not to modify the post method but only
    the other post helper methods. The process is: post_validated_form validates the form and
    returns the answer, then post_code_if_form_valid or post_code_if_form_invalid is run
    depending on the validation of the form, finally post_code_render renders the page."""
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context["game_nav_display_answer"] = False

        if not self.game.playable and not self.context["user_is_session_admin"]:
            raise Http404("The game is not playable and the user is not an admin.")

    def post_validated_form(self, request) -> (bool, object):
        pass

    def post_code_if_form_valid(self, request, form_object):
        pass

    def post_code_if_form_invalid(self, request, form_object):
        pass

    def post_code_render(self, request):
        pass

    def post(self, request, *args, **kwargs):
        success, form_object = self.post_validated_form(request)
        if success:
            self.post_code_if_form_valid(request, form_object)
            game = self.game
            if game.run_management_after_submit:
                if game.game_config().management_commands is not None:
                    for cmd_name in game.game_config().management_commands:
                        management.call_command(
                            cmd_name, session=self.session.url_tag, game=game.url_tag
                        )
        else:
            self.post_code_if_form_invalid(request, form_object)
        return self.post_code_render(request)


class GameResultsView(GameView):
    """View for seeing the results of a game. Does not do much."""
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context["game_nav_display_result"] = False

        if not self.game.results_visible and not self.context["user_is_session_admin"]:
            raise Http404(
                "The global_results are not visible and the user is not an admin."
            )
