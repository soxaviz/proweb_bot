import telebot
from telebot import types
from django.utils import timezone
from .models import UserAdmin, Group, Course, Message
from .message import *


TOKEN = '7961570181:AAGP3LOMEp1S7wjF9K9AzGD1v8aazy8tmiI'
bot = telebot.TeleBot(TOKEN)


def is_admin(user_id):

    try:
        user = UserAdmin.objects.get(telegram_id=user_id)
        return user.is_admin

    except UserAdmin.DoesNotExist:
        return False


@bot.message_handler(commands=['start'])
def start(message):

    telegram_id = message.from_user.id
    user = UserAdmin.objects.filter(telegram_id=telegram_id).first()

    if not user:
        user = UserAdmin(telegram_id=telegram_id, is_admin=False, notified=False)
        user.save()

    if not user.is_admin:
        if not user.notified:
            invite_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            button_yes = types.KeyboardButton("Согласен")
            button_no = types.KeyboardButton("Отказываюсь")
            invite_markup.add(button_yes, button_no)
            bot.send_message(telegram_id, INVITE_PROMPT, reply_markup=invite_markup)
            user.notified = True
            user.save()
        else:
            bot.send_message(telegram_id, ALREADY_ADMIN)
    else:
        send_admin_panel(telegram_id)


@bot.message_handler(func=lambda message: message.text in ["Согласен", "Отказываюсь"])
def handle_invite_response(message):

    telegram_id = message.from_user.id
    user = UserAdmin.objects.get(telegram_id=telegram_id)

    if message.text == "Согласен":
        user.is_admin = True
        user.accepted = True
        user.admin_since = timezone.now()
        user.save()
        bot.send_message(telegram_id, CONFIRM_ADMIN)
        send_admin_panel(telegram_id)
    else:
        bot.send_message(telegram_id, CANCEL_ADMIN)


def send_admin_panel(telegram_id):

    user = UserAdmin.objects.filter(telegram_id=telegram_id).first()

    if user and user.is_admin:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_courses = types.KeyboardButton("Выбрать курс")
        button_send = types.KeyboardButton("Отправить рассылку")
        button_manage = types.KeyboardButton("Управление сообщениями")
        markup.add(button_courses, button_send, button_manage)

        bot.send_message(telegram_id, WELCOME_TEXT, reply_markup=markup)
    else:
        bot.send_message(telegram_id, "Вы не были одобрены как администратор.")


@bot.message_handler(func=lambda message: message.text == "Выбрать курс")
def choose_course(message):
    telegram_id = message.from_user.id
    if not is_admin(telegram_id):
        bot.send_message(telegram_id, NO_PERMISSION)

        return

    courses = Course.objects.all()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for course in courses:
        markup.add(types.KeyboardButton(course.title))

    bot.send_message(telegram_id, COURSES_PROMPT, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Отправить рассылку")
def start_broadcast(message):

    telegram_id = message.from_user.id

    if not is_admin(telegram_id):
        bot.send_message(telegram_id, NO_PERMISSION)
        return

    bot.send_message(telegram_id, "Пожалуйста, введите текст для рассылки.")


def choose_course_for_broadcast(message, text):
    telegram_id = message.from_user.id
    if not is_admin(telegram_id):
        bot.send_message(telegram_id, NO_PERMISSION)
        return

    course = Course.objects.get(title=message.text)
    groups = Group.objects.filter(course=course)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for group in groups:
        markup.add(types.KeyboardButton(group.name))

    bot.send_message(telegram_id, "Выберите группу для отправки сообщения:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda msg: send_message_to_group(msg, text))


def send_message_to_group(message, text):
    telegram_id = message.from_user.id
    if not is_admin(telegram_id):
        bot.send_message(telegram_id, NO_PERMISSION)
        return

    group = Group.objects.get(name=message.text)

    bot.send_message(group.telegram_group_id, text)
    Message.objects.create(user=UserAdmin.objects.get(telegram_id=telegram_id), group=group, text=text)
    bot.send_message(telegram_id, "Сообщение успешно отправлено в группу.")


@bot.message_handler(func=lambda message: message.text == "Управление сообщениями")
def manage_messages(message):
    telegram_id = message.from_user.id
    if not is_admin(telegram_id):
        bot.send_message(telegram_id, NO_PERMISSION)
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_delete = types.KeyboardButton("Удалить сообщение")
    button_pin = types.KeyboardButton("Закрепить сообщение")
    button_back = types.KeyboardButton("Назад в меню")
    markup.add(button_delete, button_pin, button_back)

    bot.send_message(telegram_id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ["Удалить сообщение", "Закрепить сообщение"])
def handle_manage_actions(message):
    telegram_id = message.from_user.id
    if not is_admin(telegram_id):
        bot.send_message(telegram_id, NO_PERMISSION)
        return

    if message.text == "Удалить сообщение":
        bot.send_message(telegram_id, "Отправьте сообщение, которое нужно удалить.")
        bot.register_next_step_handler(message, delete_message)

    elif message.text == "Закрепить сообщение":
        bot.send_message(telegram_id, "Отправьте сообщение, которое нужно закрепить.")
        bot.register_next_step_handler(message, pin_message)


def delete_message(message):
    telegram_id = message.from_user.id
    if not is_admin(telegram_id):
        bot.send_message(telegram_id, NO_PERMISSION)
        return

    if message.reply_to_message:
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        bot.send_message(telegram_id, "Сообщение удалено.")
    else:
        bot.send_message(telegram_id, "Вы не выбрали сообщение для удаления.")


def pin_message(message):
    telegram_id = message.from_user.id
    if not is_admin(telegram_id):
        bot.send_message(telegram_id, NO_PERMISSION)
        return

    if message.reply_to_message:
        bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        bot.send_message(telegram_id, "Сообщение закреплено.")
    else:
        bot.send_message(telegram_id, "Вы не выбрали сообщение для закрепления.")

def back_keys(message):
    telegram_id = message.from_user.id
    if not is_admin(telegram_id):
        bot.send_message(telegram_id, NO_PERMISSION)
        return

    if message.reply_to_message:
        bot.back_keys_message(message.chat.id, message.reply_to_message.message_id)


bot.remove_webhook(url=http://127.0.0.1:8000)