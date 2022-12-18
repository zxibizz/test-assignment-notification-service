import datetime

from django.utils import timezone
from rest_framework import viewsets

from .models import Client, Mailing, Message
from .serializers import ClientSerializer, MailingSerializer, MessageSerializer
from .tasks import start_mailing


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class MailingViewSet(viewsets.ModelViewSet):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer

    def perform_create(self, serializer: MailingSerializer):
        if (
            serializer.start_at
            <= timezone.now()
            < (serializer.finish_at or datetime.MAXYEAR)
        ):
            start_mailing.delay(serializer.id)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
