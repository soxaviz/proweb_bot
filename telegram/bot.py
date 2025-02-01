import telebot
from telebot import types
from .models import UserAdmin, Group, Message
from django.conf import settings

TOKEN = '7961570181:AAGP3LOMEp1S7wjF9K9AzGD1v8aazy8tmiI'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(content_types=['new_chat_members'])
def test(message):

    telegram_group_id = message.chat.id
    group_title = message.chat.title

    group, created = Group.objects.get_or_create(telegram_group_id=telegram_group_id, defaults={

        'group_title': group_title,

    })


@bot.message_handler(commands=['start'])
def command_start(message):

    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    user, created = UserAdmin.objects.get_or_create(telegram_id=telegram_id, defaults={

        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'is_admin': False,

    })
    

    bot.send_message(telegram_id, "Вы успешно зарегистрированы в боте!")
    send_admin_menu(user)


@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_') or call.data.startswith('decline_'))
def handle_admin_confirmation(call):

    action, telegram_id = call.data.split('_')
    user = UserAdmin.objects.get(telegram_id=int(telegram_id))

    if action == 'accept':
        user.accepted = True
        user.is_admin = True
        user.save()
        bot.send_message(user.telegram_id,
                         "Вы успешно стали администратором бота! Теперь у вас есть доступ к функциям.")
        send_admin_menu(user)
    elif action == 'decline':
        user.is_admin = False
        user.accepted = False
        user.save()
        bot.send_message(user.telegram_id, "Вы отказались от роли администратора. Вы остаетесь обычным пользователем.")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)


@bot.message_handler(func=lambda message: message.text == "Назад")
def handle_back(message):

    user = UserAdmin.objects.get(telegram_id=message.from_user.id)
    if user.is_admin:

        send_admin_menu(user)
    else:
        bot.send_message(message.chat.id, "Вы не являетесь администратором.")


def send_admin_menu(user):

    if user.is_admin:

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

        markup.add(
            types.KeyboardButton("Выбрать группу"),
            types.KeyboardButton("Просмотреть сообщения"),
            types.KeyboardButton("Назад")
        )

        bot.send_message(user.telegram_id, "Выберите действие:", reply_markup=markup)

    else:

        bot.send_message(user.chat.id, "Вы не являетесь администратором.")


