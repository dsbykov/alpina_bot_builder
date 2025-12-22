from rest_framework.routers import DefaultRouter
from api.views import BotModelViewSet, ScenarioViewSet, StepViewSet
from django.urls import path

router = DefaultRouter()
router.register('bots', BotModelViewSet)
router.register('scenarios', ScenarioViewSet)
router.register('steps', StepViewSet)

urlpatterns = []
urlpatterns.extend(router.urls)
