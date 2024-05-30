from django.db import models

from random import shuffle


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


class Session(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=20, unique=True)
    index_page_descr = models.TextField(null=True, blank=True, default="Play to test your knowledge and compare "
                                                                       "yourself to the crowd!")
    play_page_descr = models.TextField(null=True, blank=True, default="You will be presented several questions and for "
                                                                      "each of them several alternatives. Try to find "
                                                                      "out the correct answer!")

    accuracy_js_data = models.TextField(null=True, blank=True)

    questions = models.ManyToManyField(Question, blank=True, related_name="sessions")
    num_displayed_questions = models.PositiveIntegerField()

    def questions_count(self):
        crowd_num_correct = 0
        crowd_num_wrong = 0
        for question in self.questions.all():
            crowd_answers = Answer.objects.filter(question=question, player__session=self)
            if crowd_answers.exists():
                if crowd_answers.filter(is_correct=True).count() > crowd_answers.filter(is_correct=False).count():
                    crowd_num_correct += 1
                else:
                    crowd_num_wrong += 1
        return crowd_num_wrong, crowd_num_correct

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class JSGraphData(models.Model):
    data = models.TextField(null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="questions_js_graph_data")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="js_graph_data")

    class Meta:
        ordering = ['session']

    def __str__(self):
        return "{} - {}".format(self.question, self.session)


class Player(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=20)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="players")
    questions = models.ManyToManyField(Question, blank=True, related_name="players")

    def questions_count(self):
        return self.answers.filter(is_correct=False).count(), self.answers.filter(is_correct=True).count()

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'session'), ('slug', 'session'))

    def __str__(self):
        return "{} - {}".format(self.name, self.session.slug)


class Answer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    answer = models.ForeignKey(Alternative, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['player']

    def __str__(self):
        return self.player.name + " - " + self.question.title + " - " + ("Correct" if self.is_correct else "Wrong")
