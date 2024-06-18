from django.core.management.base import BaseCommand

from goodbadgame.models import Alternative, Question


def add_logo_question(slug_prefix, title, logo_img_prefix, num_alts, correct_alt):
    alt_objs = []
    for alt_index in range(num_alts):
        alt, _ = Alternative.objects.update_or_create(
            slug=slug_prefix + "_alt" + str(alt_index + 1),
            defaults={
                "text": None,
                "image": "goodbad/logo/{}{}.png".format(
                    logo_img_prefix, str(alt_index + 1)
                ),
            },
        )
        alt_objs.append(alt)

    # Convention is that first in alt_dicts is the correct one
    question, _ = Question.objects.update_or_create(
        slug=slug_prefix,
        defaults={
            "text": None,
            "title": title,
            "correct_alt": alt_objs[correct_alt - 1],
        },
    )
    question.alternatives.clear()
    for alt in alt_objs:
        question.alternatives.add(alt)
    question.save()


class Command(BaseCommand):
    help = "Add the questions to database"

    def handle(self, *args, **options):
        add_logo_question("AH_Logo", "Albert Heijn Logo", "ah", 2, 2)
        add_logo_question("ABN_Logo", "ABN AMRO Logo", "abn", 2, 1)
        add_logo_question("NS_Logo", "Nederlandse Spoorwegen Logo", "ns", 2, 1)
        add_logo_question("OLVG_Logo", "OLVG Logo", "olvg", 2, 2)
        add_logo_question("PostNL_Logo", "PostNL Logo", "postnl", 2, 2)
        add_logo_question("Praxis_Logo", "Praxis Logo", "praxis", 2, 2)
        add_logo_question("Shell_Logo", "Shell Logo", "shell", 3, 2)
        add_logo_question("Swapfiets_Logo", "SwapFiets Logo", "swapfiets", 3, 2)
        add_logo_question("Google_Logo", "Google Logo", "google", 2, 2)
        add_logo_question("KLM_Logo", "KLM Logo", "klm", 2, 2)
        add_logo_question("Philips_Logo", "Philips Logo", "philips", 2, 2)
        add_logo_question("Salesforce_Logo", "Salesforce Logo", "salesforce", 2, 2)
        add_logo_question("Tiktok_Logo", "Tik Tok Logo", "tiktok", 2, 2)
        add_logo_question("Instagram_Logo", "Instagram Logo", "instagram", 2, 2)
        add_logo_question("Booking_Logo", "Booking.com Logo", "booking", 2, 2)
        add_logo_question("Unilever_Logo", "Unilever Logo", "unilever", 2, 2)
        add_logo_question("Spotify_Logo", "Spotify Logo", "spotify", 2, 2)
        add_logo_question("Slack_Logo", "Slack Logo", "slack", 2, 1)
        add_logo_question("Duolingo_Logo", "Duolingo Logo", "duolingo", 2, 2)
        add_logo_question("Twitter_Logo", "Twitter Logo", "twitter", 2, 2)
        self.stdout.write("All logo added")
