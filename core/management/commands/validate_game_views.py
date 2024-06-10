import sys

from django.core.management import BaseCommand

from core.models import Game


class Command(BaseCommand):
    help = "Checks whether the initial_view and view_after_submit parameter of a game are valid. " \
           "Can fix them if needed."

    def add_arguments(self, parser):
        parser.add_argument("--session_url_tag", type=str, help="Session URL tag")
        parser.add_argument("--auto-fix", action='store_true', help="If used, values are fixed automatically.")

    def handle(self, *args, **options):
        sys.stdout.write("Checking view members of the games...")
        auto_fix = options["auto_fix"]
        if "session_url_tag" in options and options["session_url_tag"] is not None:
            all_games = Game.objects.filter(session__url_tag=options["session_url_tag"])
        else:
            all_games = Game.objects.all()
        for game in all_games:
            all_views = game.all_url_names()
            if game.game_config().home_view is not None:
                home_view = game.game_config().home_view
            else:
                if "index" in all_views:
                    home_view = "index"
                else:
                    home_view = all_views[0]
            if game.initial_view not in all_views:
                self.stderr.write(f"For the game {game.name} in session {game.session.name}, the initial view is not valid")
                if auto_fix:
                    game.initial_view = home_view
            if game.view_after_submit not in all_views:
                self.stderr.write(f"For the game {game.name} in session {game.session.name}, the view after submit is not valid")
                if auto_fix:
                    game.view_after_submit = home_view
        if auto_fix:
            Game.objects.bulk_update(all_games, ["initial_view", "view_after_submit"])
            sys.stdout.write("All games fixed.")
        sys.stdout.write("...Finished.")
