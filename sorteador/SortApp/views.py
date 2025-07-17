import random, json, os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from .models import Jogador, Time
from .forms import JogadorForm, TimeForm
from django.shortcuts import get_object_or_404
from collections import defaultdict

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
        sorteio = request.session.get('sorteio_atual')
        if sorteio:
            caminho = os.path.join(settings.BASE_DIR, 'sorteios_salvos')
            os.makedirs(caminho, exist_ok=True)
            with open(os.path.join(caminho, 'sorteio_salvo.json'), 'w', encoding='utf-8') as f:
                json.dump(sorteio, f, ensure_ascii=False, indent=4)
    return redirect('sortear_times')

@csrf_exempt
def refazer_sorteio(request):
    if request.method == 'POST':
        if 'sorteio_atual' in request.session:
            del request.session['sorteio_atual']
    return redirect('sortear_times')