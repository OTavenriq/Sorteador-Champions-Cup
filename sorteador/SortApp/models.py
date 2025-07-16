from django.db import models

class Time(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    escudo = models.ImageField(upload_to='escudos/')

    def __str__(self):
        return self.nome
    
class Jogador(models.Model):
    nome = models.CharField(max_length=100)
    classificacao = models.PositiveIntegerField()
    overall = models.PositiveIntegerField()
    time = models.ForeignKey(Time, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nome
    
