import asyncio
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from config import celery_app
from notification_service.utils.mailing_client import (
    MailingClient,
    MailingMessage,
    MailingMessageStatus,
)

from .models import Client, Mailing, Message


@celery_app.task()
def start_upcoming_mailings():
    now = timezone.now()
    for mailing_id in Mailing.objects.filter(
        Q(finish_at__gt=now) | Q(finish_at=None),
        start_at__lte=now,
    ).values_list("id", flat=True):
        start_mailing.delay(mailing_id)


@celery_app.task()
@transaction.atomic()
def start_mailing(mailing_id: int):
    mailing = (
        Mailing.objects.filter(id=mailing_id, started_at=None)
        .select_for_update()
        .first()
    )
    if not mailing:
        return

    target_clients_qs = Client.objects.values_list("id", flat=True)
    if mailing.mobile_operator_code:
        target_clients_qs = target_clients_qs.filter(
            mobile_operator_code=mailing.mobile_operator_code
        )
    if mailing.tag:
        target_clients_qs = target_clients_qs.filter(tag=mailing.tag)

    for client_id in target_clients_qs:
        Message.objects.create(
            client_id=client_id,
            mailing_id=mailing_id,
            status=Message.Status.PENDING,
        )

    mailing.started_at = timezone.now()
    mailing.save()


def cancel_overdue_messages(now: datetime):
    Message.objects.filter(
        mailing__finish_at__lt=now, status=Message.Status.PENDING
    ).update(status=Message.Status.CANCELED)


@celery_app.task()
def send_upcoming_messages():
    mailing_client = MailingClient(token=settings.MAILING_SERVICE_TOKEN)
    now = timezone.now()
    cancel_overdue_messages(now)

    while True:
        messages = Message.objects.filter(
            status__in=[
                Message.Status.PENDING,
                Message.Status.FAILED,
            ],
        ).annotate(
            client_phone_number=F("client__phone_number"),
            mailing_content=F("mailing__content"),
        )[
            :200
        ]
        if not messages:
            break

        mailing_messages = [
            MailingMessage(
                msg_id=message.id,
                phone=message.client_phone_number,
                text=message.mailing_content,
            )
            for message in messages
        ]
        if not mailing_messages:
            return

        asyncio.run(mailing_client.post_message_batch(mailing_messages))

        update_messages = []
        for mailing_message in mailing_messages:
            update_messages.append(
                Message(
                    id=mailing_message.msg_id,
                    status=Message.Status.SUCCEED
                    if mailing_message.status == MailingMessageStatus.SUCCEED
                    else Message.Status.FAILED,
                    sent_at=now,
                )
            )
        if update_messages:
            Message.objects.bulk_update(update_messages, ["status", "sent_at"])
