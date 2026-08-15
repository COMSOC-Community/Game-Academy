from core.tests.helpers import make_game as _make_game
from goodbadgame.models import Alternative, Question


def make_goodbad_game(session, *, url_tag="gdbd", name="GoodBad", **kwargs):
    return _make_game(
        session, game_type="goodbadgame", url_tag=url_tag, name=name, **kwargs
    )


def make_question(slug, *, num_alts=2, correct_index=0):
    alts = [
        Alternative.objects.create(slug=f"{slug}_alt{i}", text=f"{slug} alt {i}")
        for i in range(num_alts)
    ]
    question = Question.objects.create(
        title=slug, slug=slug, correct_alt=alts[correct_index],
    )
    question.alternatives.add(*alts)
    return question
