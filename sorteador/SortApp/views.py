from django.shortcuts import render, redirect
from .models import Jogador, Time
from .forms import JogadorForm, TimeForm
from django.shortcuts import get_object_or_404

def dashboard(request):
    total_jogadores = Jogador.objects.count()
    total_times = Time.objects.count()
    return render(request, 'dashboard.html', {
        'total_jogadores': total_jogadores,
        'total_times': total_times
    })

def listar_jogadores(request):
    jogadores = Jogador.objects.all().order_by('classificacao', '-overall')
    return render(request, 'listar_jogadores.html', {'jogadores': jogadores})

def listar_times(request):
    times = Time.objects.all()
    return render(request, 'listar_times.html', {'times': times})

def cadastrar_jogador(request):
    if request.method == 'POST':
        form = JogadorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_jogadores')
    else:
        form = JogadorForm()
    return render(request, 'cadastrar_jogador.html', {'form': form})

def cadastrar_time(request):
    if request.method == 'POST':
        form = TimeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('listar_times')
    else:
        form = TimeForm()
    return render(request, 'cadastrar_time.html', {'form': form})

def editar_jogador(request, jogador_id):
    jogador = get_object_or_404(Jogador, id=jogador_id)
    if request.method == 'POST':
        form = JogadorForm(request.POST, instance=jogador)
        if form.is_valid():
            form.save()
            return redirect('listar_jogadores')
    else:
        form = JogadorForm(instance=jogador)
    return render(request, 'cadastrar_jogador.html', {'form': form, 'editando': True})