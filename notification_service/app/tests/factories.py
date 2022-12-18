import string

import factory
from factory import Faker
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ..models import Client, Mailing, Message


class MailingFactory(DjangoModelFactory):
    start_at = Faker("date")
    started_at = None
    finish_at = None
    content = FuzzyText(length=100)
    mobile_operator_code = FuzzyText(length=3, chars=string.digits)
    tag = FuzzyText(length=20)

    class Meta:
        model = Mailing


class ClientFactory(DjangoModelFactory):
    phone_number = FuzzyText(length=10, chars=string.digits)
    mobile_operator_code = FuzzyText(length=3, chars=string.digits)
    tag = FuzzyText(length=20)
    timezone = "UTC"

    class Meta:
        model = Client


class MessageFactory(DjangoModelFactory):
    status = Message.Status.PENDING
    sent_at = None
    mailing = factory.SubFactory(MailingFactory)
    client = factory.SubFactory(ClientFactory)

    class Meta:
        model = Message
