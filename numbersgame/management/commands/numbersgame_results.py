from django.core.management.base import BaseCommand
from django.db.models import Avg

from core.models import Session, Game
from core.utils import float_formatter

from numbersgame.apps import NAME
from numbersgame.models import Answer, Result


class Command(BaseCommand):
    help = (
        "Updates the values required for the global_results page, to be run each time a new answer "
        "is submitted."
    )

    def add_arguments(self, parser):
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)

    def handle(self, *args, **options):
        if not options["session"]:
            self.stderr.write(
                "ERROR: you need to give the URL tag of a session with the --session argument"
            )
            return
        session = Session.objects.filter(url_tag=options["session"])
        if not session.exists():
            self.stderr.write(
                "ERROR: no session with URL tag {} has been found".format(
                    options["session"]
                )
            )
            return
        session = session.first()

        if not options["game"]:
            self.stderr.write(
                "ERROR: you need to give the URL tag of a game with the --game argument"
            )
            return
        game = Game.objects.filter(
            session=session, url_tag=options["game"], game_type=NAME
        )
        if not game.exists():
            self.stderr.write(
                "ERROR: no game with URL tag {} has been found".format(options["game"])
            )
            return
        game = game.first()

        try:
            game.result_ng.delete()
        except Result.DoesNotExist:
            pass
        result = Result.objects.create(
            game=game,
            histo_js_data="",
        )
        game.result_ng = result

        answers = Answer.objects.filter(game=game, answer__isnull=False)

        if answers:
            categories = {}
            current_value = game.numbers_setting.lower_bound
            while current_value < game.numbers_setting.upper_bound:
                categories[current_value] = 0
                current_value += game.numbers_setting.histogram_bin_size

            average = answers.aggregate(Avg("answer"))["answer__avg"]
            corrected_average = game.numbers_setting.factor * average
            best_answers = []
            smallest_gap = game.numbers_setting.upper_bound
            for answer in answers:
                current_value = game.numbers_setting.lower_bound
                while (
                    current_value + game.numbers_setting.histogram_bin_size
                    <= answer.answer
                    and current_value + game.numbers_setting.histogram_bin_size
                    < game.numbers_setting.upper_bound
                ):
                    current_value += game.numbers_setting.histogram_bin_size
                categories[current_value] += 1

                gap = abs(answer.answer - corrected_average)
                if gap < smallest_gap:
                    smallest_gap = gap
                    best_answers = [answer]
                elif gap == smallest_gap:
                    best_answers.append(answer)
                answer.gap = gap
                answer.winner = False
                answer.save()
            for winner in best_answers:
                winner.winner = True
                winner.save()
            game.result_ng.average = average
            game.result_ng.corrected_average = corrected_average

            game.result_ng.histo_js_data = "\n".join(
                [
                    "['{}-{}', {}],".format(
                        float_formatter(key, num_digits=3),
                        float_formatter(
                            min(
                                key + game.numbers_setting.histogram_bin_size,
                                game.numbers_setting.upper_bound,
                            ),
                            num_digits=3,
                        ),
                        val,
                    )
                    for key, val in categories.items()
                ]
            )
            game.result_ng.save()
            game.save()

        self.stdout.write(
            "The global_results for the Numbers Game {} have been updated.".format(
                game.name
            )
        )
