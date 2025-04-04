from django.core.management.base import BaseCommand

from centipedegame.models import Answer, Result
from core.models import Session, Game

from centipedegame.apps import NAME
from core.utils import float_formatter


def payoffs(game, player1, player2):
    if player1.strategy_as_p1.startswith("Down"):
        return game.centi_setting.payoff_d_p1, game.centi_setting.payoff_d_p2
    elif player2.strategy_as_p2.startswith("Down"):
        return game.centi_setting.payoff_rd_p1, game.centi_setting.payoff_rd_p2
    elif player1.strategy_as_p1.endswith("Down"):
        return game.centi_setting.payoff_rrd_p1, game.centi_setting.payoff_rrd_p2
    elif player2.strategy_as_p2.endswith("Down"):
        return game.centi_setting.payoff_rrd_p1, game.centi_setting.payoff_rrrd_p2
    elif player2.strategy_as_p2.endswith("Right"):
        return game.centi_setting.payoff_rrrr_p1, game.centi_setting.payoff_rrrr_p2


class Command(BaseCommand):
    help = "Updates the values required for the global_results page, to be run each time a new answer is submitted."

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
            game.result_centi
        except Result.DoesNotExist:
            result = Result.objects.create(
                game=game,
                histo_strat1_js_data="",
                histo_strat2_js_data="",
                scores_heatmap_js_data="",
            )
            game.result_centi = result
            game.save()

        answers = Answer.objects.filter(game=game)
        if answers:
            best_score = 0
            winners = None
            strat1_histo_data = {}
            strat2_histo_data = {}
            score_heatmap_data = {}
            for answer in answers:
                total_score_as_p1 = 0
                total_score_as_p2 = 0
                for opponent in answers:
                    if answer != opponent:
                        score_as_p1, score_as_p2 = payoffs(game, answer, opponent)
                        total_score_as_p1 += score_as_p1
                        total_score_as_p2 += score_as_p2
                answer.avg_score_as_p1 = total_score_as_p1 / max(len(answers) - 1, 1)
                answer.avg_score_as_p2 = total_score_as_p2 / max(len(answers) - 1, 1)
                total_score = total_score_as_p1 + total_score_as_p2
                answer.avg_score = total_score / (
                    2 * max(len(answers) - 1, 1)
                )  # Dividing by 2 for P1 and P2
                answer.save()

                if winners is None or total_score > best_score:
                    best_score = total_score
                    winners = [answer]
                elif total_score == best_score:
                    winners.append(answer)

                if answer.strategy_as_p1 in strat1_histo_data:
                    strat1_histo_data[answer.strategy_as_p1] += 1
                else:
                    strat1_histo_data[answer.strategy_as_p1] = 1
                if answer.strategy_as_p2 in strat2_histo_data:
                    strat2_histo_data[answer.strategy_as_p2] += 1
                else:
                    strat2_histo_data[answer.strategy_as_p2] = 1
                if (
                    answer.strategy_as_p1,
                    answer.strategy_as_p2,
                ) not in score_heatmap_data:
                    score_heatmap_data[
                        (answer.strategy_as_p1, answer.strategy_as_p2)
                    ] = answer.avg_score

                answer.winning = False
                answer.save()
            for answer in winners:
                answer.winning = True
                answer.save()

            game.result_centi.histo_strat1_js_data = "\n".join(
                [
                    "['{}', {}],".format(key, value)
                    for key, value in strat1_histo_data.items()
                ]
            )
            game.result_centi.histo_strat2_js_data = "\n".join(
                [
                    "['{}', {}],".format(key, value)
                    for key, value in strat2_histo_data.items()
                ]
            )
            game.result_centi.scores_heatmap_js_data = "\n".join(
                [
                    "{{x: '{}', y: '{}', heat: {}}},".format(
                        key[1], key[0], float_formatter(value, num_digits=4)
                    )
                    for key, value in sorted(
                        score_heatmap_data.items(), key=lambda x: x[0]
                    )
                ]
            )
            game.result_centi.save()
            game.save()
