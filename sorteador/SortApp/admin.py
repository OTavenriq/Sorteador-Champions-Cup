from django.contrib import admin
from .models import Time, Jogador

admin.site.register(Time)
@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'classificacao', 'overall', 'time')
    search_fields = ('nome',)
    list_filter = ('classificacao',)