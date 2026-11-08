from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import csv

from .models import Challenge, ParticipantAttempt
from .utils import calculate_prompt_similarity
from .gemini_service import generate_mascot_live_tip, generate_challenge_data_with_gemini

def get_feedback_badge(similarity: float) -> dict:
    """Retorna etiqueta visual e mensagem empática com base na pontuação obtida."""
    if similarity >= 85.0:
        return {
            'text': 'Excelente percepção visual!',
            'bg_class': 'bg-emerald-500 text-white',
            'dot_class': 'bg-white',
            'icon': '😃'
        }
    elif similarity >= 70.0:
        return {
            'text': 'Muito perto do prompt original!',
            'bg_class': 'bg-purple-600 text-white',
            'dot_class': 'bg-white',
            'icon': '✨'
        }
    elif similarity >= 50.0:
        return {
            'text': 'Bom caminho! Refine os detalhes.',
            'bg_class': 'bg-amber-500 text-white',
            'dot_class': 'bg-white',
            'icon': '🔍'
        }
    else:
        return {
            'text': 'Início da exploração! Siga a dica da mascote.',
            'bg_class': 'bg-slate-600 text-white',
            'dot_class': 'bg-white',
            'icon': '💡'
        }

def game_index(request):
    """
    View principal do jogo 'Mermãs Digitais | MDX 2026'.
    Controla o fluxo do desafio ativo, identificação da aluna, cálculo das 3 tentativas e histórico.
    """
    # 1. Recupera o desafio ativo atual
    challenge = Challenge.objects.filter(ativo=True).first()
    
    # Se não houver desafio ativo, exibe mensagem informativa
    if not challenge:
        return render(request, 'game/no_challenge.html')

    # 2. Recupera o nome da participante atual da sessão ou requisição
    nome_participante = request.session.get('current_participant', '').strip()

    # Se for envio do formulário via POST
    if request.method == 'POST':
        action = request.POST.get('action', 'submit_prompt')

        # Ação de trocar / nova participante
        if action == 'new_participant':
            request.session.pop('current_participant', None)
            return redirect('game:index')

        # Envio de tentativa
        nome_enviado = request.POST.get('nome_participante', '').strip()
        prompt_enviado = request.POST.get('prompt_enviado', '').strip()

        if not nome_enviado:
            messages.error(request, "Por favor, digite seu Nome Completo para começar.")
            return redirect('game:index')

        # Atualiza a participante na sessão
        request.session['current_participant'] = nome_enviado
        nome_participante = nome_enviado

        # Verifica quantidade de tentativas já realizadas por este nome nesta rodada
        tentativas_existentes = ParticipantAttempt.objects.filter(
            challenge=challenge,
            nome_participante__iexact=nome_participante
        ).order_by('numero_tentativa')

        qtd_feitas = tentativas_existentes.count()

        if qtd_feitas >= 3:
            messages.warning(request, f"Você já concluiu suas 3 tentativas nesta rodada!")
            return redirect('game:index')

        if not prompt_enviado:
            messages.error(request, "Escreva seu prompt antes de enviar para avaliação.")
            return redirect('game:index')

        # 3. Executa o algoritmo de cálculo de similaridade e palavras-chave
        keywords_list = challenge.get_palavras_chave_list()
        similaridade_pct, acertadas = calculate_prompt_similarity(
            submitted_prompt=prompt_enviado,
            original_prompt=challenge.prompt_original,
            keywords_list=keywords_list
        )

        # 4. Salva o registro da tentativa
        numero_nova_tentativa = qtd_feitas + 1
        ParticipantAttempt.objects.create(
            challenge=challenge,
            nome_participante=nome_participante,
            numero_tentativa=numero_nova_tentativa,
            prompt_enviado=prompt_enviado,
            similaridade=similaridade_pct,
            palavras_acertadas=", ".join(acertadas),
            data_envio=timezone.now()
        )

        # Post-Redirect-Get para evitar reenvio acidental por F5 na máquina do estande
        return redirect('game:index')

    # 3. Busca tentativas da participante atual nesta rodada
    tentativas = []
    qtd_feitas = 0
    if nome_participante:
        tentativas = list(ParticipantAttempt.objects.filter(
            challenge=challenge,
            nome_participante__iexact=nome_participante
        ).order_by('numero_tentativa'))
        qtd_feitas = len(tentativas)

    limite_atingido = (qtd_feitas >= 3)
    proxima_tentativa = (qtd_feitas + 1) if qtd_feitas < 3 else None

    # Última tentativa e melhor tentativa
    ultima_tentativa = tentativas[-1] if tentativas else None
    melhor_tentativa = max(tentativas, key=lambda t: t.similaridade) if tentativas else None

    # Feedback dinâmico da última tentativa
    feedback_info = get_feedback_badge(ultima_tentativa.similaridade) if ultima_tentativa else None

    # Monta estrutura dos 3 slots para o card de histórico
    slots_historico = []
    for i in range(1, 4):
        attempt_i = next((t for t in tentativas if t.numero_tentativa == i), None)
        is_melhor = (attempt_i is not None and melhor_tentativa is not None and attempt_i.id == melhor_tentativa.id)
        slots_historico.append({
            'numero': i,
            'attempt': attempt_i,
            'is_melhor': is_melhor,
            'status': 'concluida' if attempt_i else ('atual' if i == proxima_tentativa else 'restante')
        })

    # Mensagem personalizada da mascote com o primeiro nome da aluna
    primeiro_nome = nome_participante.split()[0].title() if nome_participante else "Mermã"
    dica_formatada = challenge.dica_mascote.replace("{nome}", primeiro_nome)

    # Se a aluna já enviou uma tentativa anterior, o Gemini gera feedback pedagógico personalizado em tempo real!
    if ultima_tentativa and not limite_atingido:
        dica_formatada = generate_mascot_live_tip(
            nome_aluna=nome_participante,
            prompt_digitado=ultima_tentativa.prompt_enviado,
            prompt_original=challenge.prompt_original,
            palavras_acertadas=ultima_tentativa.get_palavras_acertadas_list(),
            similaridade=ultima_tentativa.similaridade,
            fallback_dica=dica_formatada
        )

    context = {
        'challenge': challenge,
        'nome_participante': nome_participante,
        'primeiro_nome': primeiro_nome,
        'tentativas': tentativas,
        'qtd_feitas': qtd_feitas,
        'proxima_tentativa': proxima_tentativa,
        'limite_atingido': limite_atingido,
        'ultima_tentativa': ultima_tentativa,
        'melhor_tentativa': melhor_tentativa,
        'feedback_info': feedback_info,
        'slots_historico': slots_historico,
        'dica_mascote': dica_formatada,
    }

    return render(request, 'game/index.html', context)

def reset_session(request):
    """Limpa a aluna atual da sessão para que uma nova participante jogue no estande."""
    request.session.pop('current_participant', None)
    return redirect('game:index')

def leaderboard(request):
    """
    Placar de Líderes / Ranking das Mermãs para projeção no telão/TV do estande.
    Exibe as melhores pontuações das alunas na rodada ativa.
    """
    challenge = Challenge.objects.filter(ativo=True).first()
    if not challenge:
        return render(request, 'game/no_challenge.html')

    # Agrupa tentativas por participante e seleciona a melhor
    attempts = ParticipantAttempt.objects.filter(challenge=challenge).order_by('nome_participante', '-similaridade')

    ranking_dict = {}
    for att in attempts:
        nome = att.nome_participante
        if nome not in ranking_dict:
            ranking_dict[nome] = {
                'nome': nome,
                'melhor_score': att.similaridade,
                'melhor_tentativa': att,
                'total_tentativas': 1,
                'data': att.data_envio
            }
        else:
            ranking_dict[nome]['total_tentativas'] += 1

    # Ordena por melhor pontuação (decrescente) e desempate por menos tentativas
    ranking = sorted(
        ranking_dict.values(),
        key=lambda x: (-x['melhor_score'], x['total_tentativas'], x['data'])
    )

    # Atribui posições e medalhas
    for idx, item in enumerate(ranking, 1):
        item['posicao'] = idx
        if idx == 1:
            item['medalha'] = '🥇'
            item['badge_class'] = 'bg-amber-100 text-amber-800 border-amber-300'
        elif idx == 2:
            item['medalha'] = '🥈'
            item['badge_class'] = 'bg-slate-200 text-slate-700 border-slate-300'
        elif idx == 3:
            item['medalha'] = '🥉'
            item['badge_class'] = 'bg-amber-50 text-amber-900 border-amber-400'
        else:
            item['medalha'] = f'{idx}º'
            item['badge_class'] = 'bg-purple-50 text-purple-700 border-purple-200'

    return render(request, 'game/ranking.html', {
        'challenge': challenge,
        'ranking': ranking,
        'total_participantes': len(ranking)
    })

def api_rodada_ativa(request):
    """
    API JSON consumida pela tela da participante para detectar em tempo real
    quando a equipe do estande ativa uma nova rodada com outra imagem de IA.
    """
    challenge = Challenge.objects.filter(ativo=True).first()
    if not challenge:
        return JsonResponse({'ativo': False, 'id': None})
    return JsonResponse({
        'ativo': True,
        'id': challenge.id,
        'numero_rodada': challenge.numero_rodada,
        'titulo': challenge.titulo,
        'imagem_url': challenge.get_image_url,
    })

def operator_login(request):
    """Tela de login bonita e intuitiva para a Equipe Mermãs."""
    if request.user.is_authenticated:
        return redirect('game:operator_desafios')

    if request.method == 'POST':
        usuario = request.POST.get('username', '').strip()
        senha = request.POST.get('password', '')

        user = authenticate(request, username=usuario, password=senha)
        if user is not None:
            login(request, user)
            messages.success(request, f"Bem-vinda à área da equipe, {user.username}!")
            return redirect('game:operator_desafios')
        else:
            messages.error(request, "Usuário ou senha incorretos. (Dica padrão: operador / mermas2026ifma)")

    return render(request, 'game/operator_login.html')

def operator_logout(request):
    """Desconecta a equipe e retorna à página principal."""
    logout(request)
    messages.info(request, "Sessão da equipe encerrada.")
    return redirect('game:index')

@login_required(login_url='game:operator_login')
def operator_desafios(request):
    """
    TELA 1 DO ADMIN / EQUIPE:
    Registro de Prompts de IA, upload de imagens e seleção com 1 clique da Rodada Ativa.
    """
    sugestao_gemini = None

    if request.method == 'POST':
        action = request.POST.get('action')

        # 1. Sugestão automática com Google Gemini
        if action == 'gemini_suggest':
            tema = request.POST.get('tema_sugestao', '').strip()
            sugestao_gemini = generate_challenge_data_with_gemini(tema)
            if sugestao_gemini:
                messages.success(request, "✨ Ideia de desafio e prompt gerados com sucesso pelo Gemini! Revise os campos e salve.")
            else:
                messages.warning(request, "Não foi possível conectar ao Gemini. Preencha manualmente.")

        # 2. Cadastro de Novo Desafio / Rodada
        elif action == 'create_challenge':
            titulo = request.POST.get('titulo', '').strip()
            numero_rodada = request.POST.get('numero_rodada', '').strip()
            estilo_tag = request.POST.get('estilo_tag', 'Estilo Mágico & Futurista').strip()
            prompt_original = request.POST.get('prompt_original', '').strip()
            palavras_chave = request.POST.get('palavras_chave', '').strip()
            dica_mascote = request.POST.get('dica_mascote', '').strip()
            imagem_url = request.POST.get('imagem_url', '').strip()
            ativar_imediatamente = (request.POST.get('ativar_imediatamente') == 'on')

            if not titulo or not prompt_original or not palavras_chave:
                messages.error(request, "Preencha todos os campos obrigatórios (Título, Prompt Original e Palavras-chave).")
            else:
                novo_desafio = Challenge.objects.create(
                    titulo=titulo,
                    numero_rodada=numero_rodada,
                    estilo_tag=estilo_tag,
                    prompt_original=prompt_original,
                    palavras_chave=palavras_chave,
                    dica_mascote=dica_mascote if dica_mascote else "Oi, {nome}! Observe as cores e formas com atenção!",
                    imagem_url=imagem_url,
                    ativo=False
                )

                # Upload de imagem por arquivo se enviado
                if 'imagem' in request.FILES:
                    novo_desafio.imagem = request.FILES['imagem']
                    novo_desafio.save()

                if ativar_imediatamente or Challenge.objects.filter(ativo=True).count() == 0:
                    novo_desafio.ativar()
                    messages.success(request, f"🎉 Desafio '{titulo}' cadastrado e ATIVADO como a rodada atual do estande!")
                else:
                    messages.success(request, f"Desafio '{titulo}' salvo com sucesso! Você pode ativá-lo quando quiser.")

                return redirect('game:operator_desafios')

        # 3. Ativar Rodada Selecionada
        elif action == 'activate_challenge':
            desafio_id = request.POST.get('challenge_id')
            desafio = get_object_or_404(Challenge, id=desafio_id)
            desafio.ativar()
            messages.success(request, f"🚀 Rodada {desafio.numero_rodada} ('{desafio.titulo}') ATIVADA! A tela das alunas foi atualizada.")
            return redirect('game:operator_desafios')

    desafios = Challenge.objects.all().order_by('-ativo', '-id')
    desafio_ativo = Challenge.objects.filter(ativo=True).first()

    return render(request, 'game/operator_desafios.html', {
        'desafios': desafios,
        'desafio_ativo': desafio_ativo,
        'sugestao_gemini': sugestao_gemini,
    })

@login_required(login_url='game:operator_login')
def operator_julgamento(request):
    """
    TELA 2 DO ADMIN / EQUIPE:
    Painel de Comparação e Julgamento.
    A equipe compara o prompt digitado pela aluna contra o prompt de referência salvo,
    avalia os cálculos de similaridade e define a vencedora/destaques da rodada.
    """
    todos_desafios = Challenge.objects.all().order_by('-ativo', '-id')
    desafio_ativo = Challenge.objects.filter(ativo=True).first()

    # Seleção da rodada por parâmetro na URL (?rodada_id=...) ou a ativa por padrão
    rodada_id = request.GET.get('rodada_id')
    if rodada_id:
        desafio_selecionado = get_object_or_404(Challenge, id=rodada_id)
    else:
        desafio_selecionado = desafio_ativo or todos_desafios.first()

    # Processamento da decisão da equipe
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'decidir_vencedor':
            attempt_id = request.POST.get('attempt_id')
            decisao = request.POST.get('decisao', 'pendente')
            observacao = request.POST.get('observacao', '').strip()

            tentativa = get_object_or_404(ParticipantAttempt, id=attempt_id)
            tentativa.decisao_equipe = decisao
            tentativa.observacao_equipe = observacao
            tentativa.save()

            messages.success(request, f"Avaliação da aluna {tentativa.nome_participante} atualizada para: {tentativa.get_decisao_equipe_display()}!")
            return redirect(f"{request.path}?rodada_id={tentativa.challenge_id}")

        elif action == 'exportar_csv':
            # Exporta CSV da rodada selecionada
            if not desafio_selecionado:
                return redirect('game:operator_julgamento')

            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="julgamento_rodada_{desafio_selecionado.numero_rodada}.csv"'
            response.write(u'\ufeff'.encode('utf8'))

            writer = csv.writer(response, delimiter=';')
            writer.writerow(['Posição', 'Participante', 'Tentativa', 'Similaridade (%)', 'Decisão da Equipe', 'Prompt Digitado', 'Palavras Acertadas', 'Observação'])

            tentativas_csv = ParticipantAttempt.objects.filter(challenge=desafio_selecionado).order_by('-similaridade')
            for idx, att in enumerate(tentativas_csv, 1):
                writer.writerow([
                    idx,
                    att.nome_participante,
                    att.numero_tentativa,
                    f"{att.similaridade:.1f}",
                    att.get_decisao_equipe_display(),
                    att.prompt_enviado.replace('\n', ' '),
                    att.palavras_acertadas,
                    att.observacao_equipe
                ])
            return response

    # Busca tentativas para a rodada selecionada ordenadas por similaridade (o mais próximo no topo)
    tentativas = []
    total_participantes_unicos = 0
    if desafio_selecionado:
        tentativas = ParticipantAttempt.objects.filter(challenge=desafio_selecionado).order_by('-similaridade', 'data_envio')
        total_participantes_unicos = tentativas.values('nome_participante').distinct().count()

    return render(request, 'game/operator_julgamento.html', {
        'todos_desafios': todos_desafios,
        'desafio_selecionado': desafio_selecionado,
        'tentativas': tentativas,
        'total_tentativas': len(tentativas),
        'total_participantes_unicos': total_participantes_unicos,
    })



