from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Session, Player, Game, Team, CustomUser

admin.site.register(Session)
admin.site.register(Player)
admin.site.register(Game)
admin.site.register(Team)


class CustomUserAdmin(UserAdmin):
    # Define the fields to display in the admin interface
    list_display = (
        "username",
        "email",
        "is_staff",
        "is_player",
        "is_guest_player",
        "is_random_player",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "is_player",
        "is_guest_player",
        "is_random_player",
    )
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("is_player", "is_guest_player", "is_random_player")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("is_player", "is_guest_player", "is_random_player")}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
