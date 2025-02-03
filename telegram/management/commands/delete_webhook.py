from django.core.management.base import BaseCommand
from ...bot import bot
from django.conf import settings

class Command(BaseCommand):

    def handle(self, *args, **options):
        bot.remove_webhook()


