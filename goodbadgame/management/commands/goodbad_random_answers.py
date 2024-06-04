from django.core.management.base import BaseCommand
from django.core import management

import random
import string

from core.models import CustomUser, Session, Game, Player
from goodbadgame.apps import NAME
from goodbadgame.models import Answer, QuestionAnswer


class Command(BaseCommand):
    help = "Randomly populates the answers of the goodbad game."

    def add_arguments(self, parser):
        parser.add_argument("n", type=int)
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)

    def handle(self, IP_NAME=None, *args, **options):
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

        num_answers = options['n']
        if num_answers <= 0:
            self.stderr.write(
                "The number of random answers to generate has to be at least 1."
            )
            return

        for _ in range(num_answers):
            player_name_prefix = "RANDOM_PLAYER_GOODBAD_"
            player_name = player_name_prefix + "a"
            while CustomUser.objects.filter(username=player_name).exists() or Player.objects.filter(name=player_name).exists():
                player_name = player_name_prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=15))
            user = CustomUser.objects.create_user(
                player_name,
                password="random_goodbad_player_password"
            )
            player = Player.objects.create(
                user=user,
                name=player_name,
                session=session
            )

            # Assign random questions
            player_answer = Answer.objects.create(game=game, player=player)
            pks = list(game.goodbad_setting.questions.values_list('pk', flat=True))
            pks = random.sample(pks, min(game.goodbad_setting.questions.count(), game.goodbad_setting.num_displayed_questions))
            player_answer.questions.add(*game.goodbad_setting.questions.filter(pk__in=pks))
            player_answer.save()

            for question in player_answer.questions.all():
                selected_alt = question.correct_alt if random.random() > 0.45 else random.choice(question.alternatives.all())
                QuestionAnswer.objects.create(
                    answer=player_answer,
                    question=question,
                    selected_alt=selected_alt,
                    is_correct=selected_alt == question.correct_alt
                )

        management.call_command("goodbad_computeresults", session=session.url_tag, game=game.url_tag)

        self.stdout.write(f"SUCCESS: {num_answers} random answers have been added.")
