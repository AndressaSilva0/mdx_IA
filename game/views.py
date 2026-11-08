from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Challenge, ParticipantAttempt
from .utils import calculate_prompt_similarity
from .gemini_service import generate_mascot_live_tip

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


