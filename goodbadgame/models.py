from random import shuffle

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Game, Player


class Alternative(models.Model):
    slug = models.CharField(max_length=50, unique=True)
    text = models.CharField(max_length=200, null=True, blank=True)
    image = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.slug


class Question(models.Model):
    title = models.CharField(max_length=40, unique=True)
    text = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=30, unique=True)
    alternatives = models.ManyToManyField(Alternative, related_name="questions")
    correct_alt = models.ForeignKey(Alternative, on_delete=models.CASCADE)

    def random_order_alternatives(self):
        res = list(self.alternatives.all())
        shuffle(res)
        return res

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Setting(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="goodbad_setting"
    )
    questions = models.ManyToManyField(
        Question, blank=True, related_name="goodbad_settings"
    )
    num_displayed_questions = models.PositiveIntegerField(default=10)


# This ensures population of tha questions after save
@receiver(post_save, sender=Setting, dispatch_uid="set_default_questions")
def set_default_questions(**kwargs):
    setting = kwargs["instance"]

    if not setting.questions.all():
        setting.questions.add(*Question.objects.all())


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
    answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, related_name="question_answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    selected_alt = models.ForeignKey(Alternative, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    submission_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["answer"]

    def __str__(self):
        return (
            self.answer.player.name
            + " - "
            + self.question.title
            + " - "
            + ("Correct" if self.is_correct else "Wrong")
        )


class Result(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="goodbad_result"
    )
    accuracy_js_data = models.TextField(null=True, blank=True)
    average_accuracy = models.FloatField(blank=True, null=True)
    crowd_num_correct = models.IntegerField(blank=True, null=True)
    crowd_accuracy = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ["game"]

    def __str__(self):
        return "{} - Results Data".format(self.game.name)


class QuestionResult(models.Model):
    result = models.ForeignKey(
        Result, on_delete=models.CASCADE, related_name="questions_result"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="results"
    )
    num_correct_answers = models.IntegerField(blank=True, null=True)
    num_wrong_answers = models.IntegerField(blank=True, null=True)
    accuracy = models.FloatField(blank=True, null=True)
    graph_js_data = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["question"]
        unique_together = ("result", "question")

    def __str__(self):
        return "{} - {} - {}".format(
            self.result.game.session, self.result.game.name, self.question.title
        )
