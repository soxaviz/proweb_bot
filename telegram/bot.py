import telebot
from telegram.models import Course, Group, UserAdmin
import re

bot = telebot.TeleBot('7961570181:AAGP3LOMEp1S7wjF9K9AzGD1v8aazy8tmiI')


@bot.message_handler(commands=['start'])
def start(message):
    user, created = UserAdmin.objects.get_or_create(telegram_id=message.from_user.id)
    if created:
        bot.reply_to(message, "Добро пожаловать! Вас зарегистрировали.")
    else:
        bot.reply_to(message, "Вы уже зарегистрированы.")


@bot.message_handler(commands=['send'])
def send_message(message):
    try:
        user = UserAdmin.objects.get(telegram_id=message.from_user.id)
    except UserAdmin.DoesNotExist:
        bot.reply_to(message, "Вы не являетесь администратором.")
        return

    if user.is_admin:

        courses = Course.objects.all()

        course_names = [f"{course.name} ({course.language})" for course in courses]
        course_buttons = [telebot.types.KeyboardButton(course_name) for course_name in course_names]

        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add(*course_buttons)

        bot.reply_to(message, "Выберите курс для рассылки:", reply_markup=markup)
    else:
        bot.reply_to(message, "У вас нет прав для рассылки сообщений.")


@bot.message_handler(func=lambda message: message.text)
def handle_course_selection(message):
    try:
        user = UserAdmin.objects.get(telegram_id=message.from_user.id)
    except UserAdmin.DoesNotExist:
        bot.reply_to(message, "Вы не зарегистрированы.")
        return

    if user.is_admin:
        course_name = message.text.split(" ")[0]
        try:
            course = Course.objects.get(name=course_name)
        except Course.DoesNotExist:
            bot.reply_to(message, f"Курс {course_name} не найден.")
            return

        groups = Group.objects.filter(course=course)

        bot.reply_to(message, "Введите сообщение, которое вы хотите отправить.")

        markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Вы выбрали курс. Напишите ваше сообщение.", reply_markup=markup)

        @bot.message_handler(func=lambda message: True)
        def handle_message_to_send(message):
            for group in groups:
                bot.send_message(group.telegram_group_id, message.text)
            bot.reply_to(message, "Сообщение отправлено в выбранные группы.")
    else:
        bot.reply_to(message, "У вас нет прав для рассылки сообщений.")


@bot.message_handler(func=lambda message: message.chat.type == 'supergroup')
def handle_group_message(message):
    group_name = message.chat.title

    pattern = r"PROWEB\.(?P<course_name>\S+)"
    match = re.match(pattern, group_name)

    if match:
        course_name = match.group('course_name')
        language = match.group('language')

        try:
            course = Course.objects.get(name=course_name, language=language)
        except Course.DoesNotExist:
            bot.send_message(message.chat.id, f"Курс {course_name} на языке {language} не найден!")
            return

        groups = Group.objects.filter(course=course)
        for group in groups:

            if group.telegram_group_id == str(message.chat.id):
                bot.send_message(group.telegram_group_id, "Ваше сообщение")
    else:
        bot.send_message(message.chat.id, "Такой группы нету.")


bot.set_webhook()

bot.polling(none_stop=True)
