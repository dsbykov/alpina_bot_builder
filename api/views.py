from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import Bot, Scenario, Step
from api.serializers import BotSerializer, ScenarioSerializer, StepSerializer


# Create your views here.

class BotModelViewSet(viewsets.ModelViewSet):
    queryset = Bot.objects.all()
    serializer_class = BotSerializer


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer

    @action(detail=True, methods=['get'])
    def steps(self, reqest, pk=None):
        if pk is not None:
            scenario = self.get_object()
            steps = Step.objects.filter(scenario=scenario)
            serializer = StepSerializer(steps, many=True)
            return Response(serializer.data)


class StepViewSet(viewsets.ModelViewSet):
    queryset = Step.objects.all()
    serializer_class = StepSerializer
