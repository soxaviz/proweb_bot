from django.contrib import admin
from .models import UserAdmin, Group, Course, Message
from .bot import bot, types


@admin.register(UserAdmin)
class UserAdminAdmin(admin.ModelAdmin):

    list_display = ('telegram_id', 'username', 'first_name', 'last_name', 'is_admin', 'accepted')
    search_fields = ('telegram_id', 'username')
    list_filter = ('is_admin', 'accepted')

    def save_model(self, request, obj, form, change):

        super().save_model(request, obj, form, change)

        if obj.is_admin and not obj.notified:

            try:

                markup = types.InlineKeyboardMarkup()

                btn_accept = types.InlineKeyboardButton(
                    'Принять', callback_data=f'accept_{obj.telegram_id}'
                )
                btn_decline = types.InlineKeyboardButton(
                    'Отказать', callback_data=f'decline_{obj.telegram_id}'
                )
                markup.add(btn_accept, btn_decline)

                bot.send_message(

                    obj.telegram_id,
                    "Вас хотят назначить администратором этого бота. Пожалуйста, подтвердите.",
                    reply_markup=markup)

                obj.notified = True
                obj.save()

            except Exception as e:
                pass




@admin.register(Group)
class Group(admin.ModelAdmin):
    list_display = ('group_title', 'telegram_group_id', 'course')
    list_display_links = ('group_title', 'telegram_group_id', 'course')
    list_filter = ('group_title',)
