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
        add_logo_question("Logo_AH", "Logo Albert Heijn", "ah", 2, 2)
        add_logo_question("Logo_ABN", "Logo ABN AMRO", "abn", 2, 1)
        add_logo_question("Logo_NS", "Logo Nederlandse Spoorwegen", "ns", 2, 1)
        add_logo_question("Logo_OLVG", "Logo OLVG", "olvg", 2, 2)
        add_logo_question("Logo_PostNL", "Logo PostNL", "postnl", 2, 2)
        add_logo_question("Logo_Praxis", "Logo Praxis", "praxis", 2, 2)
        add_logo_question("Logo_Shell", "Logo Shell", "shell", 3, 2)
        add_logo_question("Logo_Swapfiets", "Logo SwapFiets", "swapfiets", 3, 2)
        add_logo_question("Logo_Google", "Logo Google", "google", 2, 2)
        add_logo_question("Logo_KLM", "Logo KLM", "klm", 2, 2)
        add_logo_question("Logo_Philips", "Logo Philips", "philips", 2, 2)
        add_logo_question("Logo_Salesforce", "Logo Salesforce", "salesforce", 2, 2)
        add_logo_question("Logo_Tiktok", "Logo Tik Tok", "tiktok", 2, 2)
        add_logo_question("Logo_Instagram", "Logo Instagram", "instagram", 2, 2)
        add_logo_question("Logo_Booking", "Logo Booking.com", "booking", 2, 2)
        add_logo_question("Logo_Unilever", "Logo Unilever", "unilever", 2, 2)
        add_logo_question("Logo_Spotify", "Logo Spotify", "spotify", 2, 2)
        add_logo_question("Logo_Slack", "Logo Slack", "slack", 2, 1)
        add_logo_question("Logo_Duolingo", "Logo Duolingo", "duolingo", 2, 2)
        add_logo_question("Logo_Twitter", "Logo Twitter", "twitter", 2, 2)
        add_logo_question("Logo_Lego", "Logo Lego", "lego", 2, 1)
        self.stdout.write("All logo added")
