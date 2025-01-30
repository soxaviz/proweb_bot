from django.contrib import admin
from .models import UserAdmin, Group, Course


@admin.register(UserAdmin)
class UserAdmin(admin.ModelAdmin):
    list_display = ("pk", "telegram_id", "username", "is_admin")
    list_display_links = ("pk", "telegram_id", "username",)
    list_filter = ('is_admin',)


