from django.contrib import admin

from goodbadgame.models import (
    Alternative,
    Question,
    Answer,
    Result,
    QuestionResult,
    QuestionAnswer,
    Setting,
)

admin.site.register(Alternative)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Result)
admin.site.register(QuestionResult)
admin.site.register(QuestionAnswer)
admin.site.register(Setting)
