from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    # Telas das Alunas / Participantes
    path('', views.game_index, name='index'),
    path('reset/', views.reset_session, name='reset'),
    path('ranking/', views.leaderboard, name='ranking'),
    path('api/rodada-ativa/', views.api_rodada_ativa, name='api_rodada_ativa'),

    # Telas da Equipe / Admin
    path('operador/login/', views.operator_login, name='operator_login'),
    path('operador/logout/', views.operator_logout, name='operator_logout'),
    path('operador/desafios/', views.operator_desafios, name='operator_desafios'),
    path('operador/julgamento/', views.operator_julgamento, name='operator_julgamento'),
]

