from django.urls import path
from api.views import (
    bot_list, bot_create, bot_update, bot_delete,
    scenario_list, scenario_create, scenario_update, scenario_delete,
    step_list, step_create, step_update, step_delete,
)

urlpatterns = [
    # Bots
    path('bots/', bot_list, name='bot_list'),
    path('bot/create/', bot_create, name='bot_create'),
    path('bots/<int:pk>/edit/', bot_update, name='bot_update'),
    path('bots/<int:pk>/delete/', bot_delete, name='bot_delete'),

    # Scenarios
    path('scenarios/', scenario_list, name='scenario_list'),
    path('scenarios/create/', scenario_create, name='scenario_create'),
    path('scenarios/<int:pk>/edit/', scenario_update, name='scenario_update'),
    path('scenarios/<int:pk>/delete/', scenario_delete,
         name='scenario_delete'),

    # Steps
    path('steps/', step_list, name='step_list'),
    path('steps/create/', step_create, name='step_create'),
    path('steps/<int:pk>/edit/', step_update, name='step_update'),
    path('steps/<int:pk>/delete/', step_delete, name='step_delete'),
]
