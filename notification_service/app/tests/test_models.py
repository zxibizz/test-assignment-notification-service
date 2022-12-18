from collections import OrderedDict

import pytest

from ..models import Mailing, Message
from .factories import MailingFactory, MessageFactory

pytestmark = pytest.mark.django_db


def test_mailing_stats():
    mailing = MailingFactory()

    expected_stats = OrderedDict(
        [
            (Message.Status.PENDING, 4),
            (Message.Status.SUCCEED, 5),
            (Message.Status.FAILED, 2),
            (Message.Status.CANCELED, 0),
        ]
    )
    for status, count in expected_stats.items():
        for _ in range(count):
            MessageFactory(mailing=mailing, status=status)

    assert Mailing.objects.filter(pk=mailing.id).stats() == expected_stats
