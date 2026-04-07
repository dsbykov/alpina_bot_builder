import logging
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.models import Bot, Scenario, Step
from api.serializers import BotSerializer, ScenarioSerializer, StepSerializer
from django.shortcuts import redirect, render, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import models

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'home.html')


def auth_redirect(request):
    """
    Редирект с главной на страницу входа через Яндекс
    """
    return redirect(settings.SOCIAL_AUTH_LOGIN_URL)


# Стандартные вьюхи
class BotListCreateView(generics.ListCreateAPIView):
    serializer_class = BotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Админ видит всё, обычный пользователь — только свои
        if self.request.user.is_staff:
            return Bot.objects.all()
        return Bot.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ScenarioListCreateView(generics.ListCreateAPIView):
    serializer_class = ScenarioSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def steps(self, pk=None):
        if pk is not None:
            scenario = self.get_object()
            steps = Step.objects.filter(
                scenario=scenario,
                owner=self.request.user
            )
            serializer = StepSerializer(steps, many=True)
            return Response(serializer.data)

    def get_queryset(self):
        # Админ видит всё, обычный пользователь — только свои
        if self.request.user.is_staff:
            return Scenario.objects.all()
        return Scenario.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class StepListCreateView(generics.ListCreateAPIView):
    serializer_class = StepSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Админ видит всё, обычный пользователь — только свои
        if self.request.user.is_staff:
            return Step.objects.all()
        return Step.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# вьюхи для кастомных страниц
# --- BOTS ---
@login_required
def bot_list(request):
    logger.debug('GET все боты пользователя')
    bots = Bot.objects.filter(owner=request.user)
    return render(request, 'bots/list.html', {'bots': bots})


@login_required
def bot_create(request):
    if request.method == 'POST':
        logger.debug('POST новый бот')
        name = request.POST.get('name')
        token = request.POST.get('token')
        Bot.objects.create(name=name, token=token, owner=request.user)
        return redirect('bot_list')
    logger.debug('GET форма нового бота')
    return render(request, 'bots/form.html')


@login_required
def bot_update(request, pk):
    bot = get_object_or_404(Bot, pk=pk, owner=request.user)
    if request.method == 'POST':
        logger.debug(f'POST обновление бота {pk}')
        bot.name = request.POST.get('name')
        bot.description = request.POST.get('description')
        # будет автоматически зашифрован в save()
        bot.token = request.POST.get('token')
        bot.is_active = 'is_active' in request.POST  # чекбокс есть → True
        bot.save()
        messages.success(request, f'Бот "{bot.name}" успешно обновлён.')
        return redirect('bot_list')
    logger.debug(f'GET форма обновления бота {pk}')
    return render(request, 'bots/form.html', {'bot': bot})


@login_required
def bot_delete(request, pk):
    bot = get_object_or_404(Bot, pk=pk, owner=request.user)
    if request.method == 'POST':
        logger.debug(f'POST удаление бота {pk}')
        name = bot.name
        bot.delete()
        messages.success(request, f'Бот "{name}" удалён.')
        return redirect('bot_list')
    logger.warning(f'Попытка удалить бота методом отличным от POST.')
    return redirect('bot_list')


# --- SCENARIOS ---
@login_required
def scenario_list(request):
    bot_id = request.GET.get('bot_id')

    # Если bot_id есть — фильтруем по нему
    if bot_id:
        logger.debug(f'GET все сценарии связанные с ботом {bot_id}')
        bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
        scenarios = Scenario.objects.filter(bot=bot)
        return render(request,
                      'scenarios/list.html',
                      {'scenarios': scenarios, 'bot': bot}
                      )

    # Если нет — показываем все сценарии пользователя
    logger.debug('GET все сценарии пользователя')
    # bots = Bot.objects.filter(owner=request.user)
    scenarios = Scenario.objects.filter(
        owner=request.user).select_related('bot')
    return render(request, 'scenarios/list.html', {
        'scenarios': scenarios,
        'all_scenarios': True  # флаг для шаблона
    })


@login_required
def scenario_create(request):
    bot_id = request.GET.get('bot_id')
    available_bots = Bot.objects.filter(owner=request.user)

    # Если bot_id передан — используем его
    if bot_id:
        bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    else:
        bot = None  # Пока не выбран

    if request.method == 'POST':
        selected_bot_id = request.POST.get('bot_id')
        title = request.POST.get('title')

        if not title:
            logger.warning('POST сценарий без названия')
            messages.error(request, "Введите название сценария.")
            return render(request, 'scenarios/form.html', {
                'available_bots': available_bots,
                'bot': bot
            })

        # Опциональная привязка к боту
        selected_bot = None
        if selected_bot_id:
            logger.debug(f'Привязка сценария к боту {selected_bot_id}')
            selected_bot = get_object_or_404(
                Bot,
                id=selected_bot_id,
                owner=request.user
            )

        messages.success(request, f"Сценарий '{title}' создан.")
        if selected_bot:
            return redirect(
                f"{reverse('scenario_list')}?bot_id={selected_bot.id}"
            )
        logger.debug('Сценарий создан, возвращение к списку сценариев')
        return redirect('scenario_list')

    logger.debug('GET форма нового сценария')
    return render(request, 'scenarios/form.html', {
        'available_bots': available_bots,
        'bot': bot
    })


@login_required
def scenario_update(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk, owner=request.user)
    available_bots = Bot.objects.filter(owner=request.user)

    if request.method == 'POST':
        selected_bot_id = request.POST.get('bot_id')
        title = request.POST.get('title')
        description = request.POST.get('description')

        if not title:
            logger.warning('POST сценарий без названия')
            messages.error(request, "Введите название сценария.")
            return render(request, 'scenarios/form.html', {
                'scenario': scenario,
                'available_bots': available_bots,
                'bot': scenario.bot
            })

        # Обновляем бота (может быть None)
        new_bot = None
        if selected_bot_id:
            new_bot = get_object_or_404(
                Bot,
                id=selected_bot_id,
                owner=request.user
            )

        scenario.title = title
        scenario.description = description
        scenario.bot = new_bot
        scenario.save()

        logger.debug(f'Сценарий обновлён: {scenario}')
        messages.success(request, f"Сценарий '{title}' обновлён.")

        if new_bot:
            return redirect(
                f"{reverse('scenario_list')}?bot_id={scenario.bot.id}"
            )
        return redirect('scenario_list')

    return render(request, 'scenarios/form.html', {
        'scenario': scenario,
        'available_bots': available_bots,
        'bot': scenario.bot
    })


@login_required
def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk, owner=request.user)
    logger.debug(f'Сценарий определен: {scenario.title}')
    if request.method == 'POST':
        logger.debug(f'POST удаление сценария {pk}')
        try:
            name = scenario.title
            scenario.delete()
            messages.success(request, f'Сценарий "{name}" удалён.')
            logger.info(f'Сценарий "{name}" удалён.')
        except Exception as err:
            messages.error(request, f'Ошибка при удалении сценария: {err}')
            logger.info(f'Ошибка при удалении сценария: {err}')

        logger.debug('Возврат к списку сценариев из вьюхи удаления')
        return redirect('scenario_list')

    messages.info(request, "Прямой доступ к удалению запрещён.")
    return redirect('scenario_list')


# --- STEPS ---
@login_required
def step_list(request):
    scenario_id = request.GET.get('scenario_id')

    # Если scenario_id есть — фильтруем по нему
    if scenario_id:
        logger.debug(f'GET все шаги связанные с сценарием {scenario_id}')
        scenario = get_object_or_404(
            Scenario, id=scenario_id, owner=request.user)
        steps = Step.objects.filter(scenario=scenario).order_by('order')
        return render(request,
                      'steps/list.html',
                      {'steps': steps, 'scenario': scenario}
                      )

    # Если нет — показываем все шаги пользователя
    logger.debug('GET все шаги пользователя')
    steps = Step.objects.filter(owner=request.user).select_related(
        'scenario').order_by('scenario__title', 'order')

    return render(request, 'steps/list.html', {
        'steps': steps,
        'all_steps': True  # флаг для шаблона
    })


@login_required
def step_create(request):
    logger.debug('GET форма нового шага')
    scenario_id = request.GET.get('scenario_id')

    # Получаем все доступные сценарии пользователя
    available_scenarios = Scenario.objects.filter(
        owner=request.user).select_related('bot')

    # Если сценарий передан в URL — используем его
    if scenario_id:
        logger.debug(f'Сценарий определен: {scenario_id}')
        scenario = get_object_or_404(
            Scenario, id=scenario_id, owner=request.user)
    else:
        logger.debug('Сценарий не определен')
        scenario = None  # Пока не выбран

    # Вычисляем next_order, если сценарий известен
    next_order = 1
    if scenario:
        max_order = Step.objects.filter(scenario=scenario).aggregate(
            models.Max('order'))['order__max'] or 0
        next_order = max_order + 1
        logger.debug(f'Порядковый номер следующего сценария: {next_order}')

    if request.method == 'POST':
        logger.debug('POST новый шаг')
        selected_scenario_id = request.POST.get('scenario_id')
        order = request.POST.get('order')
        prompt = request.POST.get('prompt', '').strip()
        response_template = request.POST.get('response_template', '').strip()
        next_step_id = request.POST.get('next_step_id')

        # Валидация
        if not selected_scenario_id:
            logger.warning('POST шаг без сценария')
            messages.error(request, "Выберите сценарий.")
            return render(request, 'steps/form.html', {
                'available_scenarios': available_scenarios,
                'next_order': next_order,
                'scenario': scenario
            })

        selected_scenario = get_object_or_404(
            Scenario, id=selected_scenario_id, owner=request.user)

        try:
            order = int(order)
            if order < 1:
                logger.error('POST шаг с порядковым номером < 1')
                raise ValueError
        except (ValueError, TypeError) as err:
            logger.error(err)
            messages.error(
                request, "Порядковый номер должен быть положительным числом.")
            return render(request, 'steps/form.html', {
                'available_scenarios': available_scenarios,
                'next_order': next_order,
                'scenario': selected_scenario
            })

        if not prompt:
            messages.error(request, "Поле 'Запрос к GigaChat' обязательно.")
            return render(request, 'steps/form.html', {
                'available_scenarios': available_scenarios,
                'next_order': next_order,
                'scenario': selected_scenario
            })

        # Создаём шаг
        step = Step.objects.create(
            scenario=selected_scenario,
            order=order,
            prompt=prompt,
            response_template=response_template,
            owner=request.user
        )

        # Привязываем следующий шаг
        if next_step_id:
            try:
                next_step = Step.objects.get(
                    id=next_step_id, scenario=selected_scenario)
                step.next_step_id = next_step
                step.save(update_fields=['next_step_id'])
            except Step.DoesNotExist:
                messages.warning(request, "Указанный следующий шаг не найден.")

        logger.debug(f'Шаг создан: {step}')
        messages.success(
            request,
            f"Шаг '{prompt[:50]}...' создан в '\
                f'сценарии '{selected_scenario.title}'."
        )
        return redirect(
            f"{reverse('step_list')}?scenario_id={selected_scenario.id}"
        )

    # GET-запрос — отображение формы
    logger.debug('GET форма нового шага')
    return render(request, 'steps/form.html', {
        'available_scenarios': available_scenarios,
        'next_order': next_order,
        'scenario': scenario  # может быть None
    })


@login_required
def step_update(request, pk):
    step = get_object_or_404(Step, pk=pk, owner=request.user)
    available_scenarios = Scenario.objects.filter(
        owner=request.user).select_related('bot')

    if request.method == 'POST':
        logger.debug(f'POST обновление шага {pk}')
        selected_scenario_id = request.POST.get('scenario_id')
        order = request.POST.get('order')
        prompt = request.POST.get('prompt', '').strip()
        response_template = request.POST.get('response_template', '').strip()
        next_step_id = request.POST.get('next_step_id')

        if not selected_scenario_id:
            logger.warning('POST шаг без сценария')
            messages.error(request, "Выберите сценарий.")
            return render(request, 'steps/form.html', {
                'step': step,
                'available_scenarios': available_scenarios,
                'next_order': step.order
            })

        new_scenario = get_object_or_404(
            Scenario, id=selected_scenario_id, owner=request.user)

        try:
            step.order = int(order)
            if step.order < 1:
                logger.error('POST шаг с порядковым номером < 1')
                raise ValueError
        except (ValueError, TypeError) as err:
            logger.error(err)
            messages.error(
                request, "Порядковый номер должен быть положительным числом.")
            return render(request, 'steps/form.html', {
                'step': step,
                'available_scenarios': available_scenarios,
                'next_order': step.order
            })

        if not prompt:
            logger.warning('POST шаг без запроса к GigaChat')
            messages.error(request, "Поле 'Запрос к GigaChat' обязательно.")
            return render(request, 'steps/form.html', {
                'step': step,
                'available_scenarios': available_scenarios,
                'next_order': step.order
            })

        # Меняем сценарий, если изменился
        if step.scenario != new_scenario:
            step.scenario = new_scenario
            # Пересчитываем порядок в новом сценарии
            logger.debug(f'Пересчитываем порядок в новом сценарии')
            max_order = Step.objects.filter(scenario=new_scenario).aggregate(
                models.Max('order'))['order__max'] or 0
            step.order = max_order + 1

        step.prompt = prompt
        step.response_template = response_template

        # Обновляем next_step_id
        if next_step_id:
            try:
                logger.debug(f'Привязка следующего шага {next_step_id}')
                next_step = Step.objects.get(
                    id=next_step_id, scenario=new_scenario)
                step.next_step_id = next_step
            except Step.DoesNotExist:
                logger.warning('Следующий шаг не выбран')
                step.next_step_id = None
        else:
            logger.debug('Следующий шаг не выбран')
            step.next_step_id = None

        step.save()

        logger.debug(f'Шаг обновлён: {step}')
        messages.success(request, f"Шаг обновлён: '{prompt[:50]}...'")
        return redirect(
            f"{reverse('step_list')}?scenario_id={step.scenario.id}"
        )

    logger.debug(f'GET форма обновления шага {pk}')
    return render(request, 'steps/form.html', {
        'step': step,
        'scenario': step.scenario,
        'available_scenarios': available_scenarios,
        'next_order': step.order
    })


@login_required
def step_delete(request, pk):
    step = get_object_or_404(Step, pk=pk, owner=request.user)
    if request.method == 'POST':
        number = step.pk
        step.delete()
        messages.success(request, f'Шаг "{number}" удалён.')
        return redirect('step_list')
    return redirect('step_list')
