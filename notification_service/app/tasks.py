from django.conf import settings
from django.utils import timezone

from config import celery_app
from notification_service.utils.mailing_client import MailingClient

from .services import (
    MailingStarterService,
    UpcomingMailingsStarterService,
    UpcomingMessagesSenderService,
)


@celery_app.task()
def start_upcoming_mailings():
    upcoming_mailings_starter = UpcomingMailingsStarterService(
        mailing_starter=start_mailing.delay,
        get_current_datetime=timezone.now,
    )
    upcoming_mailings_starter.execute()


@celery_app.task()
def start_mailing(mailing_id: int):
    mailing_starter = MailingStarterService(get_current_datetime=timezone.now)
    mailing_starter.execute(mailing_id)


@celery_app.task()
def send_upcoming_messages():
    mailing_client = MailingClient(token=settings.MAILING_SERVICE_TOKEN)
    upcoming_messages_sender = UpcomingMessagesSenderService(
        mailing_client=mailing_client, get_current_datetime=timezone.now
    )
    upcoming_messages_sender.execute()
