from django.core.management.base import BaseCommand
from ...bot import bot
from django.conf import settings

class Command(BaseCommand):

    def handle(self, *args, **options):
        bot.set_webhook('https://2243-192-166-230-205.ngrok-free.app/webhook/')


