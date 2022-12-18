from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from notification_service.app.views import ClientViewSet, MailingViewSet, MessageViewSet
from notification_service.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("clients", ClientViewSet)
router.register("mailings", MailingViewSet)
router.register("messages", MessageViewSet)

app_name = "api"
urlpatterns = router.urls
