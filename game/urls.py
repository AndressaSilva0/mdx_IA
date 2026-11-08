from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.game_index, name='index'),
    path('reset/', views.reset_session, name='reset'),
    path('ranking/', views.leaderboard, name='ranking'),
]

