import telebot
from telebot import types
from .models import UserAdmin, Group



TOKEN = '7961570181:AAGP3LOMEp1S7wjF9K9AzGD1v8aazy8tmiI'
bot = telebot.TeleBot(TOKEN)



user_group_selection = {}
user_messages = {}


@bot.message_handler(content_types=['new_chat_members'])
def on_new_chat_members(message):

    telegram_group_id = message.chat.id
    group_title = message.chat.title
    group_type = message.chat.type

    group, created = Group.objects.get_or_create(telegram_group_id=telegram_group_id, defaults={
        'group_title': group_title,
        'group_type': group_type
    })

    if not created:

        if group.group_title != group_title:
            group.group_title = group_title

        if group.group_type != group_type:
            group.group_type = group_type

        group.save()

    else:

        bot.send_message(message.chat.id, "Данные группы были обновлены.")


@bot.message_handler(content_types=['new_chat_title'])
def on_chat_title_change(message):

    telegram_group_id = message.chat.id
    new_group_title = message.chat.title

    try:
        group = Group.objects.get(telegram_group_id=telegram_group_id)

        if group.group_title != new_group_title:
            group.group_title = new_group_title
            group.save()
            bot.send_message(message.chat.id, f"Название группы обновлено на: {new_group_title}")

    except Group.DoesNotExist:
        bot.send_message(message.chat.id, "Данные группы были обновлены.")


@bot.message_handler(content_types=['supergroup_chat_created', 'group_chat_created'])
def on_group_type_change(message):

    telegram_group_id = message.chat.id
    group_title = message.chat.title
    group_type = message.chat.type

    try:

        group = Group.objects.get(telegram_group_id=telegram_group_id)

        if group.group_type != group_type:
            group.group_type = group_type
            group.save()
            bot.send_message(message.chat.id, f"Тип группы обновлен на: {group_type}")

    except Group.DoesNotExist:

        group, created = Group.objects.get_or_create(telegram_group_id=telegram_group_id, defaults={
            'group_title': group_title,
            'group_type': group_type
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
        )

        markup.add(
            types.KeyboardButton("Выбрать личный чат студента")
        )

        markup.add(
            types.KeyboardButton("Назад")
        )

        bot.send_message(user.telegram_id, "Выберите действие:", reply_markup=markup)

    else:

        bot.send_message(user.chat.id, "Вы не являетесь администратором.")


@bot.message_handler(func=lambda message: message.text == "Выбрать группу")
def handle_choose_group(message):

    user = UserAdmin.objects.get(telegram_id=message.from_user.id)

    if not user.is_admin:
        bot.send_message(message.chat.id, "Вы не являетесь администратором.")
        return

    groups = Group.objects.all()

    if not groups:
        bot.send_message(message.chat.id, "Группы еще не добавлены в систему.")
        return

    markup = types.InlineKeyboardMarkup()

    for group in groups:
        markup.add(
            types.InlineKeyboardButton(group.group_title, callback_data=f"select_group_{group.telegram_group_id}"))

    bot.send_message(message.chat.id, "Выберите группу:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_group_'))
def handle_group_selection(call):

    group_id = call.data.split("_")[-1]
    group = Group.objects.get(telegram_group_id=group_id)

    user_group_selection[call.from_user.id] = group.telegram_group_id

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    markup.add(
        types.KeyboardButton("Отправить сообщение")
    )
    markup.add(
        types.KeyboardButton("Закрепить сообщение")
    )
    markup.add(
        types.KeyboardButton("Удалить сообщение")
    )
    markup.add(
        types.KeyboardButton("Назад")
    )

    bot.send_message(call.message.chat.id, f"Вы выбрали группу {group.group_title}. Что хотите сделать?",
                     reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Отправить сообщение")
def handle_send_message(message):

    user = UserAdmin.objects.get(telegram_id=message.from_user.id)
    group_id = user_group_selection.get(message.from_user.id)

    if group_id is None:
        bot.send_message(message.chat.id, "Вы не выбрали группу.")
        return

    msg = bot.send_message(message.chat.id, "Напишите сообщение, которое вы хотите отправить в группу.")
    bot.register_next_step_handler(msg, send_message_to_group)


def send_message_to_group(message):
    print(f'##############{message}##############')

    user = UserAdmin.objects.get(telegram_id=message.from_user.id)
    group_id = user_group_selection.get(message.from_user.id)

    if group_id is None:
        bot.send_message(message.chat.id, "Вы не выбрали группу.")
        return

    if message.text:
        sent_message = bot.send_message(group_id, message.text)
        msg_text = message.text[:50]

    elif message.photo:
        sent_message = bot.send_photo(group_id, message.photo[-1].file_id)
        msg_text = "Фото"

    elif message.video:
        sent_message = bot.send_video(group_id, message.video.file_id)
        msg_text = "Видео"

    else:
        msg_text = "Неизвестный тип сообщения"

    if group_id not in user_messages:
        user_messages[group_id] = []

    user_messages[group_id].append({
        'message_id': sent_message.message_id,
        'text': msg_text
    })

    bot.send_message(message.chat.id, "Сообщение отправлено в группу.")


@bot.message_handler(func=lambda message: message.text == "Удалить сообщение")
def handle_delete_message(message):
    user = UserAdmin.objects.get(telegram_id=message.from_user.id)
    group_id = user_group_selection.get(message.from_user.id)

    if group_id is None:
        bot.send_message(message.chat.id, "Вы не выбрали группу.")
        return

    if group_id not in user_messages or len(user_messages[group_id]) == 0:
        bot.send_message(message.chat.id, "Нет сообщений для удаления.")
        return

    markup = types.InlineKeyboardMarkup()

    for msg in user_messages[group_id]:
        msg_preview = msg['text'] if len(msg['text']) <= 50 else msg['text'][:50] + '...'
        markup.add(types.InlineKeyboardButton(f"Удалить: {msg_preview}", callback_data=f"delete_{msg['message_id']}"))

    bot.send_message(message.chat.id, "Выберите сообщение для удаления:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_message_deletion(call):

    message_id = int(call.data.split("_")[1])
    user = UserAdmin.objects.get(telegram_id=call.from_user.id)
    group_id = user_group_selection.get(call.from_user.id)

    if group_id is None:
        bot.send_message(call.message.chat.id, "Вы не выбрали группу.")
        return

    try:

        bot.delete_message(group_id, message_id)

        user_messages[group_id] = [msg for msg in user_messages[group_id] if msg['message_id'] != message_id]

        bot.send_message(call.message.chat.id, f"Сообщение {message_id} успешно удалено.")

    except Exception as e:

        bot.send_message(call.message.chat.id, f"Ошибка при удалении: {str(e)}")

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)


@bot.message_handler(func=lambda message: message.text == "Закрепить сообщение")
def handle_pin_message(message):

    user = UserAdmin.objects.get(telegram_id=message.from_user.id)
    group_id = user_group_selection.get(message.from_user.id)

    if group_id is None:
        bot.send_message(message.chat.id, "Вы не выбрали группу.")
        return

    msg = bot.send_message(message.chat.id, "Напишите сообщение, которое вы хотите закрепить.")
    print(f"soxa$$$$$$$$$$${msg}soxa$$$$$$$$$$$$$$")

    bot.register_next_step_handler(msg, pin_message_in_group)


def pin_message_in_group(message):

    user = UserAdmin.objects.get(telegram_id=message.from_user.id)
    group_id = user_group_selection.get(message.from_user.id)

    if group_id is None:
        bot.send_message(message.chat.id, "Вы не выбрали группу.")
        return

    if message.text:

        sent_message = bot.send_message(group_id, message.text)

    elif message.photo:

        sent_message = bot.send_photo(group_id, message.photo[-1].file_id)

    elif message.video:

        sent_message = bot.send_video(group_id, message.video.file_id)

    bot.pin_chat_message(group_id, sent_message.message_id)
    bot.send_message(message.chat.id, "Сообщение закреплено в группе.")
    print(f"-------{sent_message}-----")


@bot.message_handler(func=lambda message: message.text == "Выбрать личный чат студента")
def handle_choose_student(message):

    user = UserAdmin.objects.get(telegram_id=message.from_user.id)

    if not user.is_admin:
        bot.send_message(message.chat.id, "Вы не являетесь администратором.")
        return

    users = UserAdmin.objects.filter(is_admin=False)

    if not users:
        bot.send_message(message.chat.id, "Нет пользователей для выбора.")
        return

    markup = types.InlineKeyboardMarkup()

    for student in users:

        markup.add(types.InlineKeyboardButton(f"{student.first_name} {student.last_name}",
                                              callback_data=f"select_student_{student.telegram_id}"))

    bot.send_message(message.chat.id, "Выберите студента:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Выбрать личный чат студента")
def handle_choose_student(message):
    user = UserAdmin.objects.get(telegram_id=message.from_user.id)

    if not user.is_admin:
        bot.send_message(message.chat.id, "Вы не являетесь администратором.")
        return

    users = UserAdmin.objects.filter(is_admin=False)
    if not users:
        bot.send_message(message.chat.id, "Нет пользователей для выбора.")
        return

    markup = types.InlineKeyboardMarkup()
    for student in users:
        markup.add(types.InlineKeyboardButton(f"{student.first_name} {student.last_name}",
                                              callback_data=f"select_student_{student.telegram_id}"))

    bot.send_message(message.chat.id, "Выберите студента:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_student_'))
def handle_student_selection(call):

    student_id = int(call.data.split("_"))

    student = UserAdmin.objects.get(telegram_id=student_id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    markup.add(
        types.KeyboardButton("Отправить сообщение")
    )

    markup.add(
        types.KeyboardButton("Удалить сообщение")
    )

    markup.add(
        types.KeyboardButton("Назад")
    )

    bot.edit_message_reply_markup(call.message.chat.id, call.message.student, reply_markup=None)




