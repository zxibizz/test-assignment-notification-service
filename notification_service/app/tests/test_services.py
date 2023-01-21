from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from django.utils import timezone

from notification_service.app.models import Mailing, Message
from notification_service.app.services import (
    MailingStarterCallable,
    MailingStarterService,
    UpcomingMailingsStarterService,
    UpcomingMessagesSenderService,
)
from notification_service.app.tests.factories import (
    ClientFactory,
    MailingFactory,
    MessageFactory,
)
from notification_service.app.tests.mocks import TestMailingClient

pytestmark = pytest.mark.django_db

NOW = timezone.make_aware(datetime(2022, 1, 1))
MONTH = timedelta(days=30)


def _get_time_awared_now():
    return NOW


def test_upcoming_mailings_starter_service(settings):
    mock_mailing_starter = Mock(spec=MailingStarterCallable)

    expected_mailings_ids = [
        MailingFactory(start_at=NOW - MONTH).id,
        MailingFactory(start_at=NOW - MONTH, finish_at=NOW + MONTH).id,
    ]
    MailingFactory(start_at=NOW + MONTH)
    MailingFactory(start_at=NOW - MONTH * 2, finish_at=NOW - MONTH)

    upcoming_mailings_starter = UpcomingMailingsStarterService(
        mock_mailing_starter, _get_time_awared_now
    )
    upcoming_mailings_starter.execute()

    assert [
        call_args[0][0] for call_args in mock_mailing_starter.call_args_list
    ] == expected_mailings_ids


def test_mailing_starter_service_ignores_already_handled_mailing():
    now = datetime(2022, 1, 1)
    mailing_starter = MailingStarterService(lambda: now)

    ClientFactory(
        tag="tag",
        mobile_operator_code="123",
    )
    mailing_id = MailingFactory(
        started_at=now - MONTH,
        tag="tag",
        mobile_operator_code="123",
    ).id

    mailing_starter.execute(mailing_id)
    assert not Message.objects.count()


@pytest.mark.parametrize("is_empty_tag", [True, False])
@pytest.mark.parametrize("is_empty_mobile_operator_code", [True, False])
def test_mailing_starter_service(is_empty_tag, is_empty_mobile_operator_code):
    target_tag = "some_tag"
    target_mobile_operator_code = "123"
    for tag in (target_tag, "another_tag"):
        for mobile_operator_code in (target_mobile_operator_code, "234"):
            ClientFactory(
                tag=tag,
                mobile_operator_code=mobile_operator_code,
            )
    ClientFactory(tag="completely_another_tag", mobile_operator_code="987")
    mailing_id = MailingFactory(
        start_at=NOW - MONTH,
        tag=None if is_empty_tag else target_tag,
        mobile_operator_code=None
        if is_empty_mobile_operator_code
        else target_mobile_operator_code,
    ).id
    mailing_starter = MailingStarterService(lambda: NOW)
    mailing_starter.execute(mailing_id)

    created_messages = Message.objects.filter(
        mailing_id=mailing_id,
    ).select_related("client")

    for message in created_messages:
        if not is_empty_tag:
            assert message.client.tag == target_tag
        if not is_empty_mobile_operator_code:
            assert message.client.mobile_operator_code == target_mobile_operator_code
        assert created_messages[0].status == Message.Status.PENDING

    assert Mailing.objects.get(id=mailing_id).started_at == NOW


def test_upcoming_messages_sender_service():
    overdue_message = MessageFactory(
        mailing=MailingFactory(start_at=NOW - MONTH * 2, finish_at=NOW - MONTH)
    )
    due_mailing_with_finish_date = MailingFactory(
        start_at=NOW - MONTH, finish_at=NOW + MONTH
    )
    due_mailing_with_no_finish_date = MailingFactory(
        start_at=NOW - MONTH, finish_at=None
    )
    due_messages = [
        MessageFactory(mailing=due_mailing_with_finish_date),
        MessageFactory(mailing=due_mailing_with_no_finish_date),
    ]

    test_mailing_client = TestMailingClient()

    upcoming_messages_sender = UpcomingMessagesSenderService(
        test_mailing_client, _get_time_awared_now
    )
    upcoming_messages_sender.execute()

    overdue_message.refresh_from_db()
    assert overdue_message.status == Message.Status.CANCELED

    for message, posted_mailing_message in zip(
        due_messages, test_mailing_client.posted_messages
    ):
        assert message.id == posted_mailing_message.msg_id
        assert message.client.phone_number == posted_mailing_message.phone
        assert message.mailing.content == posted_mailing_message.text

        message.refresh_from_db()
        assert message.status == Message.Status.SUCCEED
