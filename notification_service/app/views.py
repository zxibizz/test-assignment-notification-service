import datetime

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Client, Mailing, Message
from .serializers import (
    ClientSerializer,
    MailingSerializer,
    MailingsStatsSerializer,
    MailingStatsSerializer,
    MessageSerializer,
)
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

    @extend_schema(responses=MailingsStatsSerializer(many=False))
    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = MailingsStatsSerializer(
            {"message_statuses": queryset.stats(), "count": queryset.count()}
        )
        return Response(serializer.data)

    @extend_schema(responses=MailingStatsSerializer(many=False))
    @action(detail=True, methods=["get"])
    def detail_stats(self, request, pk):
        serializer = MailingStatsSerializer(
            {"message_statuses": self.get_queryset().filter(id=pk).stats()}
        )
        return Response(serializer.data)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
