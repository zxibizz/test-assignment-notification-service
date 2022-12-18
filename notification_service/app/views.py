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


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class MailingViewSet(viewsets.ModelViewSet):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer

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
