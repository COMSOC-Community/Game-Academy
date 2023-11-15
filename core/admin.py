from django.contrib import admin

from .models import Session, Player, Game, Team, CustomUser

admin.site.register(Session)
admin.site.register(Player)
admin.site.register(Game)
admin.site.register(Team)
admin.site.register(CustomUser)