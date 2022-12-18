from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask, PeriodicTasks


class Command(BaseCommand):
    help = "Creates periodic tasks"

    def handle(self, *args, **options):
        IntervalSchedule.objects.all().delete()
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.SECONDS,
        )

        task, _ = PeriodicTask.objects.get_or_create(
            name="Start upcoming mailings",
            task="notification_service.app.tasks.start_upcoming_mailings",
            interval=schedule,
        )
        PeriodicTasks.changed(task)
        task, _ = PeriodicTask.objects.get_or_create(
            name="Send upcoming messages",
            task="notification_service.app.tasks.send_upcoming_messages",
            interval=schedule,
        )
        PeriodicTasks.changed(task)
