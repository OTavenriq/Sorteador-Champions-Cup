from django.db import models

class Time(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    escudo = models.ImageField(upload_to='escudos/')
    grupo = models.CharField(max_length=10, null=True)

    def __str__(self):
        return self.nome
    
class Jogador(models.Model):
    nome = models.CharField(max_length=100)
    classificacao = models.PositiveIntegerField()
    overall = models.PositiveIntegerField()
    time = models.ForeignKey(Time, on_delete=models.SET_NULL, related_name='jogadores', null=True, blank=True)

    def __str__(self):
        return self.nome
    
class Jogo(models.Model):
    time_a = models.ForeignKey(
        Time, on_delete=models.CASCADE, related_name='jogos_como_a'
    )
    time_b = models.ForeignKey(
        Time, on_delete=models.CASCADE, related_name='jogos_como_b'
    )
    ordem = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.time_a} x {self.time_b}"