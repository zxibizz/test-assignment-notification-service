from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import Client, Mailing, Message


class ClientSerializer(ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "phone_number",
            "mobile_operator_code",
            "tag",
            "timezone",
        ]


class MailingSerializer(ModelSerializer):
    class Meta:
        model = Mailing
        fields = [
            "id",
            "start_at",
            "started_at",
            "finish_at",
            "content",
            "mobile_operator_code",
            "tag",
        ]
        read_only_fields = ["started_at"]


class MessageSerializer(ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "created_at",
            "sent_at",
            "status",
            "mailing",
            "client",
        ]
        read_only_fields = fields


class MessagesStatusesSerializer(serializers.Serializer):
    Pending = serializers.IntegerField()
    Succeed = serializers.IntegerField()
    Failed = serializers.IntegerField()
    Canceled = serializers.IntegerField()


class MailingStatsSerializer(serializers.Serializer):
    message_statuses = MessagesStatusesSerializer()


class MailingsStatsSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    message_statuses = MessagesStatusesSerializer()
