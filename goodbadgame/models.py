from django.db import models

from random import shuffle

from core.models import Game, Player


class Alternative(models.Model):
    slug = models.CharField(max_length=50, unique=True)
    text = models.CharField(max_length=200, null=True, blank=True)
    image = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        ordering = ['slug']

    def __str__(self):
        return self.slug


class Question(models.Model):
    title = models.CharField(max_length=40, unique=True)
    text = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=30, unique=True)
    alternatives = models.ManyToManyField(Alternative, related_name='questions')
    correct_alt = models.ForeignKey(Alternative, on_delete=models.CASCADE)

    def random_order_alternatives(self):
        res = list(self.alternatives.all())
        shuffle(res)
        return res

    def crowd_count(self, session):
        crowd_answers = Answer.objects.filter(question=self, player__session=session)
        if crowd_answers.exists():
            return crowd_answers.filter(is_correct=False).count(), crowd_answers.filter(is_correct=True).count()
        else:
            return 0, 0

    class Meta:
        ordering = ['title']

    def __str__(self):
        return "{} - {}".format(self.title, self.slug)


class Setting(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="goodbad_setting"
    )
    questions = models.ManyToManyField(Question, blank=True, related_name="goodbad_settings")
    num_displayed_questions = models.PositiveIntegerField()


class Answer(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="goodbad_answers"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="goodbad_answer"
    )
    questions = models.ManyToManyField(Question, blank=True, related_name="players")
    score = models.IntegerField(blank=True, null=True)
    accuracy = models.FloatField(blank=True, null=True)


class QuestionAnswer(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="question_answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_alt = models.ForeignKey(Alternative, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    submission_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['answer']

    def __str__(self):
        return self.answer.player.name + " - " + self.question.title + " - " + ("Correct" if self.is_correct else "Wrong")


class Result(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="goodbad_result"
    )
    accuracy_js_data = models.TextField(null=True, blank=True)
    crowd_accuracy = models.FloatField(blank=True, null=True)

    def questions_count(self):
        crowd_num_correct = 0
        crowd_num_wrong = 0
        for question in self.game.goodbad_setting.questions.all():
            crowd_answers = Answer.objects.filter(question=question, player__session=self)
            if crowd_answers.exists():
                if crowd_answers.filter(is_correct=True).count() > crowd_answers.filter(is_correct=False).count():
                    crowd_num_correct += 1
                else:
                    crowd_num_wrong += 1
        return crowd_num_wrong, crowd_num_correct

    class Meta:
        ordering = ["game"]

    def __str__(self):
        return "{} - Results Data".format(self.game.name)


class QuestionGraphData(models.Model):
    result = models.ForeignKey(
        Result, on_delete=models.CASCADE, related_name="questions_graph_data"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE,
                                 related_name="js_graph_data")
    data = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['session']

    def __str__(self):
        return "{} - {} - {}".format(self.result.game.session, self.result.game.name, self.question.title)

