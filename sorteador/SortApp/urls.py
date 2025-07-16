from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('jogadores/', views.listar_jogadores, name='listar_jogadores'),
    path('times/', views.listar_times, name='listar_times'),
    path('jogadores/novo/', views.cadastrar_jogador, name='cadastrar_jogador'),
    path('times/novo/', views.cadastrar_time, name='cadastrar_time'),
    path('jogadores/editar/<int:jogador_id>/', views.editar_jogador, name='editar_jogador'),
]
