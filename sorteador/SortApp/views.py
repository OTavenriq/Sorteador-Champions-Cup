import random, json, os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from collections import defaultdict
from django.contrib import messages
from .models import Jogador, Time
from .forms import JogadorForm, TimeForm


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
    MARGEM_MAXIMA = 30

    for tentativa in range(MAX_TENTATIVAS):
        sorteio = {time.id: {'time': time, 'jogadores': [], 'overall': 0} for time in times}
        usado_por_time = {time.id: set() for time in times}
        sucesso = True

        for pote, jogadores_pote in potes.items():
            jogadores_disp = jogadores_pote[:]
            random.shuffle(jogadores_disp)

            for jogador in jogadores_disp:
                pesos, candidatos = [], []

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
            break
    else:
        return render(request, 'sorteador/resultado.html', {
            'erro': f'Não foi possível gerar um sorteio com margem menor que {MARGEM_MAXIMA} após {MAX_TENTATIVAS} tentativas.'})

    aviso = None
    if margem > MARGEM_MAXIMA:
        aviso = f'Atenção: diferença de overall entre os times é de {margem} pontos, acima da margem ideal de {MARGEM_MAXIMA}.'

    # 🔹 salva o sorteio na sessão para persistir o resultado exibido
    request.session['sorteio_atual'] = {
        str(tid): [j.id for j in info['jogadores']]
        for tid, info in sorteio.items()
    }

    return render(request, 'sorteador/resultado.html', {
        'sorteio': sorteio,
        'aviso': aviso
    })


@csrf_exempt
def salvar_sorteio(request):
    if request.method == 'POST':
        sorteio_atual = request.session.get('sorteio_atual')

        if not sorteio_atual:
            return render(request, 'sorteador/resultado.html', {
                'erro': 'Nenhum sorteio ativo para salvar.'
            })

        # 🔹 limpa vínculos anteriores
        Jogador.objects.update(time=None)

        # 🔹 aplica o sorteio que estava salvo na sessão
        for time_id, jogadores_ids in sorteio_atual.items():
            time = Time.objects.get(id=int(time_id))
            jogadores = Jogador.objects.filter(id__in=jogadores_ids)
            overall_total = sum(j.overall for j in jogadores)

            time.overall = overall_total
            time.save()

            for j in jogadores:
                j.time = time
                j.save()

        # 🔹 limpa a sessão após salvar
        if 'sorteio_atual' in request.session:
            del request.session['sorteio_atual']

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

import random
from collections import defaultdict

def sortear_grupos(request):
    times = list(Time.objects.prefetch_related('jogadores').all())

    if not times:
        return render(request, 'sorteador/grupos.html', {
            'erro': 'Cadastre os times antes de sortear os grupos.'
        })

    NUM_GRUPOS = 2
    MAX_TENTATIVAS = 100
    MARGEM_MAXIMA = 5  # margem da MEDIA de overall

    if len(times) < NUM_GRUPOS:
        return render(request, 'sorteador/grupos.html', {
            'erro': 'Quantidade de times insuficiente para formar os grupos.'
        })

    # 🔹 calcula media de overall de cada time
    times_info = []
    for time in times:
        jogadores = time.jogadores.all()
        if jogadores.exists():
            media = sum(j.overall for j in jogadores) / jogadores.count()
        else:
            media = 0

        times_info.append({
            'time': time,
            'media': round(media, 1)
        })

    for tentativa in range(MAX_TENTATIVAS):
        grupos = {
            f'Grupo {chr(65+i)}': {
                'times': [],
                'soma_media': 0
            }
            for i in range(NUM_GRUPOS)
        }

        sucesso = True
        times_disp = times_info[:]
        random.shuffle(times_disp)

        for info_time in times_disp:
            pesos = []
            candidatos = []

            MAX_POR_GRUPO = len(times) // NUM_GRUPOS

            for grupo, dados in grupos.items():
                if len(dados['times']) < MAX_POR_GRUPO:
                    peso = 1 / (dados['soma_media'] + 1)
                    candidatos.append(grupo)
                    pesos.append(peso)

            if not candidatos:
                sucesso = False
                break

            grupo_escolhido = random.choices(candidatos, weights=pesos, k=1)[0]
            grupos[grupo_escolhido]['times'].append(info_time)
            grupos[grupo_escolhido]['soma_media'] += info_time['media']

        if not sucesso:
            continue

        medias = [
            dados['soma_media'] / len(dados['times'])
            for dados in grupos.values()
            if dados['times']
        ]

        margem = max(medias) - min(medias)

        if margem <= MARGEM_MAXIMA:
            break
    else:
        return render(request, 'sorteador/grupos.html', {
            'erro': f'Não foi possível gerar grupos equilibrados após {MAX_TENTATIVAS} tentativas.'
        })

    # 🔹 salva na sessão
    request.session['grupos_sorteados'] = {
        grupo: [t['time'].id for t in dados['times']]
        for grupo, dados in grupos.items()
    }

    return render(request, 'sorteador/grupos.html', {
        'grupos': grupos,
        'margem': round(margem, 2)
    })

@csrf_exempt
def salvar_grupos(request):
    if request.method == 'POST':
        grupos_sorteados = request.session.get('grupos_sorteados')

        if not grupos_sorteados:
            messages.error(request, 'Nenhum sorteio de grupos ativo para salvar.')
            return redirect('sortear_grupos')

        # 🔹 limpa grupos anteriores
        Time.objects.update(grupo=None)

        # 🔹 aplica os grupos salvos na sessão
        for grupo, times_ids in grupos_sorteados.items():
            for time_id in times_ids:
                time = Time.objects.get(id=time_id)
                time.grupo = grupo
                time.save()

        # 🔹 limpa a sessão
        del request.session['grupos_sorteados']

        messages.success(request, 'Sorteio dos grupos salvo com sucesso!')

    return redirect('listar_grupos')

from collections import defaultdict

def listar_grupos(request):
    times = Time.objects.prefetch_related('jogadores').all()

    grupos = defaultdict(lambda: {
        'times': [],
        'soma_medias': 0
    })

    for time in times:
        if time.grupo:
            jogadores = time.jogadores.all()
            if jogadores.exists():
                media_time = round(
                    sum(j.overall for j in jogadores) / jogadores.count(), 1
                )
            else:
                media_time = 0

            grupos[time.grupo]['times'].append({
                'time': time,
                'media': media_time
            })
            grupos[time.grupo]['soma_medias'] += media_time

    # 🔹 calcula média final de cada grupo
    for grupo, dados in grupos.items():
        total_times = len(dados['times'])
        dados['media_grupo'] = round(
            dados['soma_medias'] / total_times, 1
        ) if total_times else 0

    return render(request, 'sorteador/listar_grupos.html', {
        'grupos': dict(grupos)
    })
