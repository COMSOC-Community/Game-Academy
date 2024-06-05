import re
import sys

from django.contrib.staticfiles import finders
from django.core.management import BaseCommand

from core.models import Game


class Command(BaseCommand):
    help = "Checks whether the illustration paths in the database exist. Can fix them if needed."

    def add_arguments(self, parser):
        parser.add_argument("--auto-fix", action='store_true', help="If used, illustration paths are fixed automatically.")

    def handle(self, *args, **options):
        sys.stdout.write("Checking illustration paths of the game...")
        auto_fix = options["auto_fix"]
        all_games = Game.objects.all()
        for game in all_games:
            illustration_path = game.illustration_path
            if illustration_path is not None:
                found = finders.find(illustration_path)
                if found is None:
                    self.stderr.write(f"For the game {game} of type {game.game_type}, the path has not been found in the static folder.")
                    if auto_fix:
                        potential_paths = []
                        for potential_path in game.game_config().illustration_paths:
                            found_potential = finders.find(potential_path)
                            if found_potential is not None:
                                potential_paths.append(potential_path)
                        if len(potential_paths) == 0:
                            self.stderr.write(f"None of the path in the game app for {game} of type {game.game_type} have been found in the static folder.")
                            break
                        path_number = re.findall(r'\d+', illustration_path)
                        new_illustration_path = ''
                        if path_number:
                            path_number = path_number[-1]
                            for potential_path in potential_paths:
                                potential_number = re.findall(r'\d+', potential_path)
                                if potential_number:
                                    if path_number == potential_number[-1]:
                                        new_illustration_path = potential_path
                                        break
                        if not new_illustration_path:
                            new_illustration_path = potential_paths[0]
                        game.illustration_path = new_illustration_path
                        self.stderr.write(f"\tWe changed it from {illustration_path} to {new_illustration_path}")
        if auto_fix:
            Game.objects.bulk_update(all_games, ["illustration_path"])
        sys.stdout.write("...Finished.")
