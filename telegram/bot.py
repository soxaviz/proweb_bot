import telebot
import re
from django.conf import settings
from .models import UserAdmin, Group, Course
from telebot import types

bot = telebot.TeleBot(settings.TELEGRAM_TOKEN)



bot.message_handler(commands=['start'])
def start_mess(message):
    bot.reply_to(message, 'Вас приветствует учебный центр PROWEB')