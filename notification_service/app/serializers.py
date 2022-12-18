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
            "finish_at",
            "content",
            "mobile_operator_code",
            "tag",
        ]


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
