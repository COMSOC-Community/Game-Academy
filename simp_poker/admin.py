from django.contrib import admin

from .models import Setting, Answer, Result

admin.site.register(Setting)
admin.site.register(Result)
admin.site.register(Answer)
