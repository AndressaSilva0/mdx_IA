from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    # Telas das Alunas / Participantes
    path('', views.game_index, name='index'),
    path('reset/', views.reset_session, name='reset'),
    path('ranking/', views.leaderboard, name='ranking'),
    path('api/rodada-ativa/', views.api_rodada_ativa, name='api_rodada_ativa'),
    path('api/gerar-ideia-ia/', views.api_gerar_ideia_ia, name='api_gerar_ideia_ia'),
    path('api/otimizar-prompt-imagem/', views.api_otimizar_prompt_imagem, name='api_otimizar_prompt_imagem'),

    # Alternância de Modalidade (Equipe / Participante via Senha de 6 Dígitos)
    path('equipe/entrar-pin/', views.trocar_modalidade_equipe, name='trocar_modalidade_equipe'),
    path('equipe/sair/', views.sair_modalidade_equipe, name='sair_modalidade_equipe'),

    # Telas da Equipe / Admin
    path('operador/login/', views.operator_login, name='operator_login'),
    path('operador/logout/', views.operator_logout, name='operator_logout'),
    path('operador/desafios/', views.operator_desafios, name='operator_desafios'),
    path('operador/julgamento/', views.operator_julgamento, name='operator_julgamento'),
]

