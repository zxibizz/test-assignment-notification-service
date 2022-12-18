from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from ..models import Mailing, Message
from ..tasks import send_upcoming_messages, start_mailing, start_upcoming_mailings
from .factories import ClientFactory, MailingFactory, MessageFactory
from .mocks import TestMailingClient

pytestmark = pytest.mark.django_db


def test_start_upcoming_mailings(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    now = datetime(2022, 2, 1)

    expected_mailings_ids = [
        MailingFactory(start_at=datetime(2022, 1, 1)).id,
        MailingFactory(
            start_at=datetime(2022, 1, 1), finish_at=datetime(2022, 3, 1)
        ).id,
    ]
    MailingFactory(start_at=datetime(2022, 4, 1))
    MailingFactory(start_at=datetime(2022, 1, 1), finish_at=datetime(2022, 1, 15))

    with freeze_time(now), patch(
        "notification_service.app.tasks.start_mailing.delay"
    ) as mock_start_mailing:
        start_upcoming_mailings()

    assert [
        call_args[0][0] for call_args in mock_start_mailing.call_args_list
    ] == expected_mailings_ids


def test_start_mailing_ignores_already_handled_mailing():
    ClientFactory(
        tag="tag",
        mobile_operator_code="123",
    )
    mailing_id = MailingFactory(
        started_at=datetime(2022, 1, 1),
        tag="tag",
        mobile_operator_code="123",
    ).id
    start_mailing(mailing_id)
    assert not Message.objects.count()


@pytest.mark.parametrize("is_empty_tag", [True, False])
@pytest.mark.parametrize("is_empty_mobile_operator_code", [True, False])
def test_start_mailing_filters(is_empty_tag, is_empty_mobile_operator_code):
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
        start_at=datetime(2022, 1, 1),
        tag=None if is_empty_tag else target_tag,
        mobile_operator_code=None
        if is_empty_mobile_operator_code
        else target_mobile_operator_code,
    ).id
    now = datetime(2022, 1, 2)
    with freeze_time(now):
        start_mailing(mailing_id)

    created_messages = Message.objects.filter(
        mailing_id=mailing_id,
    ).select_related("client")

    for message in created_messages:
        if not is_empty_tag:
            assert message.client.tag == target_tag
        if not is_empty_mobile_operator_code:
            assert message.client.mobile_operator_code == target_mobile_operator_code
        assert created_messages[0].status == Message.Status.PENDING

    assert Mailing.objects.get(id=mailing_id).started_at == timezone.make_aware(now)


def test_send_upcoming_messages():
    now = datetime(2022, 2, 1)
    overdue_message = MessageFactory(
        mailing=MailingFactory(
            start_at=now - timedelta(days=20),
            finish_at=now - timedelta(days=10),
        )
    )
    due_mailing_with_finish_date = MailingFactory(
        start_at=now - timedelta(days=20),
        finish_at=now + timedelta(days=10),
    )
    due_mailing_with_no_finish_date = MailingFactory(
        start_at=now - timedelta(days=20), finish_at=None
    )
    due_messages = [
        MessageFactory(mailing=due_mailing_with_finish_date),
        MessageFactory(mailing=due_mailing_with_no_finish_date),
    ]

    test_mailing_client = TestMailingClient()
    with freeze_time(now), patch(
        "notification_service.app.tasks.MailingClient", return_value=test_mailing_client
    ):
        send_upcoming_messages()

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
