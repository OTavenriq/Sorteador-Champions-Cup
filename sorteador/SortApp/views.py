import random, json, os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from .models import Jogador, Time
from .forms import JogadorForm, TimeForm
from django.shortcuts import get_object_or_404
from collections import defaultdict
from django.contrib import messages

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

def sortear_times(request):
    jogadores = list(Jogador.objects.all())
    times = list(Time.objects.all())

    if not jogadores or not times:
        return render(request, 'sorteador/resultado.html', {'erro': 'Cadastre jogadores e times antes de sortear.'})

    potes = defaultdict(list)
    for jogador in jogadores:
        potes[jogador.classificacao].append(jogador)

    num_times = len(times)

    for pote, lista in potes.items():
        if len(lista) < num_times:
            return render(request, 'sorteador/resultado.html', {
                'erro': f'Pote {pote} tem apenas {len(lista)} jogadores. São necessários {num_times}.'})

    MAX_TENTATIVAS = 100
    MARGEM_MAXIMA = 25

    for tentativa in range(MAX_TENTATIVAS):
        sorteio = {time.id: {'time': time, 'jogadores': [], 'overall': 0} for time in times}
        usado_por_time = {time.id: set() for time in times}

        sucesso = True

        for pote, jogadores_pote in potes.items():
            jogadores_disp = jogadores_pote[:]
            random.shuffle(jogadores_disp)

            for jogador in jogadores_disp:
                pesos = []
                candidatos = []

                for time_id, info in sorteio.items():
                    if pote not in usado_por_time[time_id]:
                        peso = 1 / (info['overall'] + 1)
                        candidatos.append(time_id)
                        pesos.append(peso)

                if not candidatos:
                    sucesso = False
                    break

                time_escolhido = random.choices(candidatos, weights=pesos, k=1)[0]
                sorteio[time_escolhido]['jogadores'].append(jogador)
                sorteio[time_escolhido]['overall'] += jogador.overall
                usado_por_time[time_escolhido].add(pote)

            if not sucesso:
                break

        if not sucesso:
            continue

        overalls = [info['overall'] for info in sorteio.values()]
        margem = max(overalls) - min(overalls)

        if margem <= MARGEM_MAXIMA:
            aviso = None
            break
    else:
        return render(request, 'sorteador/resultado.html', {
            'erro': f'Não foi possível gerar um sorteio com margem menor que {MARGEM_MAXIMA} após {MAX_TENTATIVAS} tentativas.'})

    if margem > MARGEM_MAXIMA:
        aviso = f'Atenção: diferença de overall entre os times é de {margem} pontos, acima da margem ideal de {MARGEM_MAXIMA}.'
    else:
        aviso = None

    return render(request, 'sorteador/resultado.html', {
        'sorteio': sorteio,
        'aviso': aviso
    })

@csrf_exempt
def salvar_sorteio(request):
    if request.method == 'POST':
        jogadores = Jogador.objects.all()
        for jogador in jogadores:
            jogador.time = None
            jogador.save()

        jogadores = list(Jogador.objects.all())
        times = list(Time.objects.all())

        potes = defaultdict(list)
        for jogador in jogadores:
            potes[jogador.classificacao].append(jogador)

        num_times = len(times)
        MAX_TENTATIVAS = 100
        MARGEM_MAXIMA = 25

        for tentativa in range(MAX_TENTATIVAS):
            sorteio = {time.id: {'time': time, 'jogadores': [], 'overall': 0} for time in times}
            usado_por_time = {time.id: set() for time in times}
            sucesso = True

            for pote, jogadores_pote in potes.items():
                jogadores_disp = jogadores_pote[:]
                random.shuffle(jogadores_disp)

                for jogador in jogadores_disp:
                    pesos = []
                    candidatos = []

                    for time_id, info in sorteio.items():
                        if pote not in usado_por_time[time_id]:
                            peso = 1 / (info['overall'] + 1)
                            candidatos.append(time_id)
                            pesos.append(peso)

                    if not candidatos:
                        sucesso = False
                        break

                    time_escolhido = random.choices(candidatos, weights=pesos, k=1)[0]
                    sorteio[time_escolhido]['jogadores'].append(jogador)
                    sorteio[time_escolhido]['overall'] += jogador.overall
                    usado_por_time[time_escolhido].add(pote)

                if not sucesso:
                    break

            if not sucesso:
                continue

            overalls = [info['overall'] for info in sorteio.values()]
            margem = max(overalls) - min(overalls)

            if margem <= MARGEM_MAXIMA:
                for time_id, info in sorteio.items():
                    time = info['time']
                    time.overall = info['overall']
                    time.save()
                    for jogador in info['jogadores']:
                        jogador.time = time
                        jogador.save()
                break
        else:
            return render(request, 'sorteador/resultado.html', {
                'erro': f'Falha ao salvar sorteio com margem menor que {MARGEM_MAXIMA}.'})

    return redirect('listar_times')

@csrf_exempt
def refazer_sorteio(request):
    if request.method == 'POST':
        if 'sorteio_atual' in request.session:
            del request.session['sorteio_atual']
    return redirect('sortear_times')

def detalhes_time(request, time_id):
    time = get_object_or_404(Time, id=time_id)
    jogadores = time.jogadores.all().order_by('classificacao', '-overall')
    overall_total = sum(j.overall for j in jogadores)
    return render(request, 'detalhes_time.html', {
        'time': time,
        'jogadores': jogadores,
        'overall_total': overall_total,
    })

@csrf_exempt
def excluir_todos_jogadores(request):
    if request.method == 'POST':
        Jogador.objects.all().delete()
        messages.success(request, 'Todos os jogadores foram excluídos com sucesso!')
    return redirect('listar_jogadores')

def listar_times_completos(request):
    times = Time.objects.prefetch_related('jogadores').all()
    times_com_overall = []

    for time in times:
        jogadores = time.jogadores.all()
        if jogadores.exists():
            soma = sum(j.overall for j in jogadores)
            media = round(soma / len(jogadores), 1)
        else:
            media = 0

        times_com_overall.append({
            'obj': time,
            'overall_total': media
        })

    context = {
        'times_com_overall': times_com_overall,
    }
    return render(request, 'times_completos.html', context)
