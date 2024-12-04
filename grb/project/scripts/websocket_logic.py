import asyncio
from django.core.management.base import BaseCommand
from project.views import scheduled_fetch  # Import from your views file

class Command(BaseCommand):
    help = "Run WebSocket scheduled fetch"

    def handle(self, *args, **kwargs):
        try:
            print("Starting WebSocket scheduled fetcher...")
            asyncio.run(scheduled_fetch())
        except KeyboardInterrupt:
            print("Fetcher stopped by user.")
