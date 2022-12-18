from collections import OrderedDict

import pytz
from django.db import models
from django.db.models import Count, QuerySet

TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))


class MailingQuerySet(QuerySet):
    def stats(self) -> dict["Message.Status", int]:
        stats_qs = (
            Message.objects.filter(mailing__in=self)
            .values("status")
            .annotate(count=Count("status"))
        )
        result = OrderedDict([(val, 0) for val in Message.Status.values])
        for stat in stats_qs:
            result[stat["status"]] = stat["count"]

        return result


class Mailing(models.Model):
    start_at = models.DateTimeField(blank=False, null=False)
    started_at = models.DateTimeField(blank=True, null=True)
    finish_at = models.DateTimeField(blank=True, null=True)
    content = models.TextField(null=False)
    mobile_operator_code = models.CharField(max_length=3, null=True)
    tag = models.CharField(max_length=50, null=True)

    objects = MailingQuerySet.as_manager()


class Client(models.Model):
    phone_number = models.CharField(max_length=10)
    mobile_operator_code = models.CharField(max_length=3)
    tag = models.CharField(max_length=50)
    timezone = models.CharField(max_length=32, choices=TIMEZONES, default="UTC")


class Message(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending"
        SUCCEED = "Succeed"
        FAILED = "Failed"
        CANCELED = "Canceled"

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.TextField(choices=Status.choices)
    mailing = models.ForeignKey(Mailing, on_delete=models.PROTECT)
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
