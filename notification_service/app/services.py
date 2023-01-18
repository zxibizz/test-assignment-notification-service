import asyncio
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from django.db import transaction
from django.db.models import F, Q, QuerySet
from more_itertools import batched

from notification_service.utils.mailing_client import (
    MailingClient,
    MailingMessage,
    MailingMessageStatus,
)
from notification_service.utils.services import BaseService

from .models import Client, Mailing, Message


class GetCurrentDateTimeCallable(Protocol):
    def __call__(self) -> datetime:
        ...


class MailingStarterCallable(Protocol):
    def __call__(self, mailing_id):
        ...


class UpcomingMailingsStarterService(BaseService):
    def __init__(
        self,
        mailing_starter: MailingStarterCallable,
        get_current_datetime: GetCurrentDateTimeCallable,
    ):
        self.mailing_starter = mailing_starter
        self.get_current_datetime = get_current_datetime

    def execute(self):
        for mailing_id in self._get_upcoming_mailings():
            self.mailing_starter(mailing_id)

    def _get_upcoming_mailings(self) -> list[int]:
        now = self.get_current_datetime()
        return Mailing.objects.filter(
            Q(finish_at__gt=now) | Q(finish_at=None),
            start_at__lte=now,
        ).values_list("id", flat=True)


class MailingStarterService(BaseService):
    def __init__(self, get_current_datetime: GetCurrentDateTimeCallable):
        self.get_current_datetime = get_current_datetime

    @staticmethod
    def _get_pending_mailing(mailing_id: int) -> Mailing | None:
        return (
            Mailing.objects.filter(id=mailing_id, started_at=None)
            .select_for_update()
            .first()
        )

    @staticmethod
    def _get_target_clients(mailing: Mailing) -> QuerySet:
        target_clients_qs = Client.objects.values_list("id", flat=True)
        if mailing.mobile_operator_code:
            target_clients_qs = target_clients_qs.filter(
                mobile_operator_code=mailing.mobile_operator_code
            )
        if mailing.tag:
            target_clients_qs = target_clients_qs.filter(tag=mailing.tag)
        return target_clients_qs

    @staticmethod
    def _create_mailing_message(client_id: int, mailing_id: int):
        Message.objects.create(
            client_id=client_id,
            mailing_id=mailing_id,
            status=Message.Status.PENDING,
        )

    @transaction.atomic()
    def execute(self, mailing_id: int):
        mailing = self._get_pending_mailing(mailing_id=mailing_id)
        if not mailing:
            return

        for client_id in self._get_target_clients(mailing=mailing):
            self._create_mailing_message(client_id=client_id, mailing_id=mailing_id)

        mailing.started_at = self.get_current_datetime()
        mailing.save()


class UpcomingMessagesSender(BaseService):
    def __init__(
        self,
        mailing_client: MailingClient,
        get_current_datetime: GetCurrentDateTimeCallable,
    ):
        self.mailing_client = mailing_client
        self.get_current_datetime = get_current_datetime

    @staticmethod
    def _cancel_overdue_messages(now: datetime):
        Message.objects.filter(
            mailing__finish_at__lt=now, status=Message.Status.PENDING
        ).update(status=Message.Status.CANCELED)

    @staticmethod
    def _get_message_batches(batch_size: int) -> Iterable[Iterable[Message]]:
        messages_qs = Message.objects.filter(
            status__in=[
                Message.Status.PENDING,
                Message.Status.FAILED,
            ],
        )

        if not messages_qs.count():
            return []

        return batched(
            messages_qs.annotate(
                client_phone_number=F("client__phone_number"),
                mailing_content=F("mailing__content"),
            ).iterator(chunk_size=batch_size),
            batch_size,
        )

    def _get_mailing_message_batches(
        self, batch_size: int
    ) -> Iterable[Iterable[MailingMessage]]:
        for message_batch in self._get_message_batches(batch_size):
            mailing_messages = [
                MailingMessage(
                    msg_id=message.id,
                    phone=message.client_phone_number,  # noqa - annotated
                    text=message.mailing_content,  # noqa - annotated
                )
                for message in message_batch
            ]
            yield mailing_messages
        else:
            yield from ()

    def _send_messages(self, messages: Iterable[MailingMessage]):
        asyncio.run(
            self.mailing_client.post_message_batch(messages),
        )

    @staticmethod
    def _update_sent_messages(
        mailing_messages: Iterable[MailingMessage], now: datetime
    ):
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

    def execute(self):
        now = self.get_current_datetime()
        self._cancel_overdue_messages(now)

        for mailing_messages in self._get_mailing_message_batches(200):
            self._send_messages(mailing_messages)
            self._update_sent_messages(mailing_messages=mailing_messages, now=now)
