from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import csv

from .models import Challenge, ParticipantAttempt
from .utils import calculate_prompt_similarity, generate_ai_image_url, download_and_save_ai_image
from .gemini_service import generate_mascot_live_tip, generate_challenge_data_with_gemini, optimize_prompt_for_image_model

def check_equipe_permission(request):
    """Verifica se o operador está autenticado via PIN de 6 dígitos ou login."""
    return bool(request.session.get('is_equipe') or request.user.is_authenticated)

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

def get_challenge_ranking(challenge):
    """
    Retorna a lista de ranking das alunas para um desafio,
    ordenada pela melhor pontuação de cada participante (com desempate por menos tentativas e data de envio).
    Identifica as 3 primeiras colocadas que receberão o prêmio no fim da rodada.
    """
    if not challenge:
        return []

    attempts = ParticipantAttempt.objects.filter(challenge=challenge).order_by('email_participante', 'nome_participante', '-similaridade')

    ranking_dict = {}
    for att in attempts:
        chave_unica = (att.email_participante or att.nome_participante).lower().strip()
        if chave_unica not in ranking_dict:
            ranking_dict[chave_unica] = {
                'nome': att.nome_participante,
                'email': att.email_participante,
                'melhor_score': att.similaridade,
                'melhor_tentativa': att,
                'total_tentativas': 1,
                'data': att.data_envio
            }
        else:
            ranking_dict[chave_unica]['total_tentativas'] += 1

    ranking = sorted(
        ranking_dict.values(),
        key=lambda x: (-x['melhor_score'], x['total_tentativas'], x['data'])
    )

    for idx, item in enumerate(ranking, 1):
        item['posicao'] = idx
        if idx == 1:
            item['medalha'] = '🥇'
            item['premio_label'] = '1º Lugar (Prêmio Ouro) 🏆'
            item['badge_class'] = 'bg-[#FEBE01] text-[#1E0B36] border-2 border-[#1E0B36]'
            item['is_top3'] = True
        elif idx == 2:
            item['medalha'] = '🥈'
            item['premio_label'] = '2º Lugar (Prêmio Prata) 🥈'
            item['badge_class'] = 'bg-slate-200 text-[#1E0B36] border-2 border-[#1E0B36]'
            item['is_top3'] = True
        elif idx == 3:
            item['medalha'] = '🥉'
            item['premio_label'] = '3º Lugar (Prêmio Bronze) 🥉'
            item['badge_class'] = 'bg-amber-100 text-[#1E0B36] border-2 border-[#1E0B36]'
            item['is_top3'] = True
        else:
            item['medalha'] = f'{idx}º'
            item['premio_label'] = 'Classificada'
            item['badge_class'] = 'bg-[#FAF5FF] text-[#6D28D9] border border-purple-200'
            item['is_top3'] = False

    return ranking

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

    # 2. Recupera a participante atual da sessão ou requisição
    nome_participante = request.session.get('current_participant', '').strip()
    email_participante = request.session.get('current_email', '').strip().lower()

    # Se for envio do formulário via POST
    if request.method == 'POST':
        action = request.POST.get('action', 'submit_prompt')

        # Ação de trocar / nova participante
        if action == 'new_participant':
            request.session.pop('current_participant', None)
            request.session.pop('current_email', None)
            return redirect('game:index')

        # Ação de salvar participante explicitamente
        if action == 'save_participant':
            nome_enviado = request.POST.get('nome_participante', '').strip()
            email_enviado = request.POST.get('email_participante', '').strip().lower()

            if not nome_enviado or not email_enviado:
                messages.error(request, "Por favor, preencha seu Nome Completo e E-mail para salvar.")
                return redirect('game:index')

            request.session['current_participant'] = nome_enviado
            request.session['current_email'] = email_enviado

            qtd = ParticipantAttempt.objects.filter(challenge=challenge, email_participante=email_enviado).count()
            if qtd >= 3:
                messages.warning(request, f"Olá {nome_enviado}! Você já concluiu suas 3 tentativas nesta rodada. Sua melhor pontuação está salva no Ranking oficial!")
            elif qtd > 0:
                messages.success(request, f"Olá {nome_enviado}! Participante salva. Você já realizou {qtd} de 3 tentativas.")
            else:
                messages.success(request, f"🎉 Participante {nome_enviado} salva com sucesso! Você tem 3 tentativas para tentar acertar o prompt.")

            return redirect('game:index')

        # Envio de tentativa
        nome_enviado = request.POST.get('nome_participante', '').strip()
        email_enviado = request.POST.get('email_participante', '').strip().lower()
        prompt_enviado = request.POST.get('prompt_enviado', '').strip()

        if not nome_enviado or not email_enviado:
            messages.error(request, "Por favor, preencha seu Nome Completo e E-mail para participar.")
            return redirect('game:index')

        # Atualiza a participante na sessão
        request.session['current_participant'] = nome_enviado
        request.session['current_email'] = email_enviado
        nome_participante = nome_enviado
        email_participante = email_enviado

        # Verifica quantidade de tentativas já realizadas por este e-mail nesta rodada
        tentativas_existentes = ParticipantAttempt.objects.filter(
            challenge=challenge,
            email_participante=email_participante
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

        # 4. Salva o registro da tentativa vinculando nome e e-mail
        numero_nova_tentativa = qtd_feitas + 1
        ParticipantAttempt.objects.create(
            challenge=challenge,
            nome_participante=nome_participante,
            email_participante=email_participante,
            numero_tentativa=numero_nova_tentativa,
            prompt_enviado=prompt_enviado,
            similaridade=similaridade_pct,
            palavras_acertadas=", ".join(acertadas),
            data_envio=timezone.now()
        )

        return redirect('game:index')

    # 3. Busca tentativas da participante atual nesta rodada (por e-mail ou nome)
    tentativas = []
    qtd_feitas = 0
    if email_participante:
        tentativas = list(ParticipantAttempt.objects.filter(
            challenge=challenge,
            email_participante=email_participante
        ).order_by('numero_tentativa'))
        qtd_feitas = len(tentativas)
    elif nome_participante:
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

    # 4. Calcula o Ranking da Rodada e Top 3 que ganham prêmio no fim da rodada
    ranking_geral = get_challenge_ranking(challenge)
    ranking_top3 = ranking_geral[:3]
    total_participantes_rodada = len(ranking_geral)

    # Identifica a posição da aluna atual no ranking da rodada
    minha_posicao_ranking = None
    if email_participante or nome_participante:
        chave_atual = (email_participante or nome_participante).lower().strip()
        minha_posicao_ranking = next(
            (r for r in ranking_geral if (r['email'].lower() == chave_atual or r['nome'].lower() == chave_atual)),
            None
        )

    context = {
        'challenge': challenge,
        'nome_participante': nome_participante,
        'email_participante': email_participante,
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
        'ranking_top3': ranking_top3,
        'minha_posicao_ranking': minha_posicao_ranking,
        'total_participantes_rodada': total_participantes_rodada,
        'is_equipe': check_equipe_permission(request),
    }

    return render(request, 'game/index.html', context)

def reset_session(request):
    """Limpa a aluna atual da sessão para que uma nova participante jogue no estande."""
    request.session.pop('current_participant', None)
    request.session.pop('current_email', None)
    return redirect('game:index')

def leaderboard(request):
    """
    Placar de Líderes / Ranking das Mermãs para projeção no telão/TV do estande.
    Exibe as melhores pontuações das alunas na rodada ativa e destaca o Top 3 que ganham prêmio.
    """
    challenge = Challenge.objects.filter(ativo=True).first()
    if not challenge:
        return render(request, 'game/no_challenge.html')

    ranking = get_challenge_ranking(challenge)

    # Identifica se a equipe já homologou uma vencedora oficial para esta rodada
    vencedora_oficial = ParticipantAttempt.objects.filter(
        challenge=challenge,
        decisao_equipe='vencedora'
    ).first()

    return render(request, 'game/ranking.html', {
        'challenge': challenge,
        'ranking': ranking,
        'ranking_top3': ranking[:3],
        'ranking_restante': ranking[3:],
        'total_participantes': len(ranking),
        'vencedora_oficial': vencedora_oficial
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

def api_gerar_ideia_ia(request):
    """
    Endpoint AJAX: Gera com Google Gemini uma nova ideia de rodada, prompt de referência,
    palavras-chave e dica da mascote, além da imagem correspondente, sem recarregar a página.
    """
    if not check_equipe_permission(request):
        return JsonResponse({'sucesso': False, 'erro': 'Não autorizado.'}, status=403)

    tema = request.GET.get('tema', '').strip()
    dados = generate_challenge_data_with_gemini(tema)

    if not dados or not dados.get('prompt_original'):
        return JsonResponse({'sucesso': False, 'erro': 'Não foi possível gerar ideia no momento.'}, status=500)

    # Identifica o melhor prompt visual em inglês para o gerador de imagem
    visual_en = dados.get('prompt_visual_en')
    if not visual_en:
        visual_en = optimize_prompt_for_image_model(dados['prompt_original'])

    dados['prompt_visual_en'] = visual_en
    dados['imagem_url'] = generate_ai_image_url(visual_en)

    return JsonResponse({'sucesso': True, 'dados': dados})

def api_otimizar_prompt_imagem(request):
    """
    Endpoint AJAX: Traduz e refina o prompt em português para inglês com o Gemini
    e retorna a URL de imagem gerada por IA correspondente.
    """
    if not check_equipe_permission(request):
        return JsonResponse({'sucesso': False, 'erro': 'Não autorizado.'}, status=403)

    prompt_pt = request.GET.get('prompt', '').strip()
    if not prompt_pt:
        return JsonResponse({'sucesso': False, 'erro': 'Prompt vazio.'}, status=400)

    import time
    seed = int(request.GET.get('seed', time.time()))
    visual_en = optimize_prompt_for_image_model(prompt_pt)
    img_url = generate_ai_image_url(visual_en, seed=seed)

    return JsonResponse({
        'sucesso': True,
        'prompt_en': visual_en,
        'imagem_url': img_url
    })

def trocar_modalidade_equipe(request):
    """
    Alterna para a modalidade 'Equipe' mediante conferência da Senha de 6 Dígitos.
    Isso substitui logins complexos na máquina do estande por um PIN rápido e seguro.
    Suporta tanto requisições AJAX (com balão flutuante imediato) quanto formulário padrão.
    """
    if request.method == 'POST':
        pin_enviado = request.POST.get('pin', '').strip()
        pin_correto = str(getattr(settings, 'EQUIPE_PIN', '262026')).strip()
        is_ajax = (request.headers.get('x-requested-with') == 'XMLHttpRequest' or 
                   'application/json' in request.headers.get('Accept', ''))

        if pin_enviado == pin_correto:
            request.session['is_equipe'] = True
            messages.success(request, "🔓 Modo Equipe ativado com sucesso! Bem-vinda à área técnica.")
            if is_ajax:
                from django.urls import reverse
                return JsonResponse({'sucesso': True, 'redirect_url': reverse('game:operator_desafios')})
            return redirect('game:operator_desafios')
        else:
            msg_erro = "Senha de 6 dígitos incorreta! Digite o PIN da equipe do estande."
            if is_ajax:
                return JsonResponse({'sucesso': False, 'mensagem': msg_erro}, status=400)
            messages.error(request, msg_erro)
            return redirect('game:index')

    return redirect('game:index')

def sair_modalidade_equipe(request):
    """Alterna de volta para a modalidade 'Participante'."""
    request.session['is_equipe'] = False
    messages.info(request, "Modo Participante ativado.")
    return redirect('game:index')

def operator_login(request):
    """Tela de login alternativa para a Equipe Mermãs."""
    if check_equipe_permission(request):
        return redirect('game:operator_desafios')

    if request.method == 'POST':
        usuario = request.POST.get('username', '').strip()
        senha = request.POST.get('password', '')

        user = authenticate(request, username=usuario, password=senha)
        if user is not None:
            login(request, user)
            request.session['is_equipe'] = True
            messages.success(request, f"Bem-vinda à área da equipe, {user.username}!")
            return redirect('game:operator_desafios')
        else:
            messages.error(request, "Usuário ou senha incorretos.")

    return render(request, 'game/operator_login.html')

def operator_logout(request):
    """Desconecta a equipe e retorna à página principal."""
    logout(request)
    request.session['is_equipe'] = False
    messages.info(request, "Sessão da equipe encerrada.")
    return redirect('game:index')

def operator_desafios(request):
    """
    TELA 1 DO ADMIN / EQUIPE:
    Registro de Prompts de IA, upload de imagens e seleção com 1 clique da Rodada Ativa.
    """
    if not check_equipe_permission(request):
        messages.warning(request, "Acesso restrito. Informe a senha de 6 dígitos para entrar no Modo Equipe.")
        return redirect('game:index')

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
                elif imagem_url:
                    novo_desafio.imagem_url = imagem_url
                    novo_desafio.save()
                else:
                    # Se não informou arquivo nem URL, gera automaticamente a imagem com IA a partir do prompt otimizado!
                    import time
                    rel_path = f"challenges/desafio_{novo_desafio.id}_{int(time.time())}.jpg"
                    prompt_otimizado = optimize_prompt_for_image_model(prompt_original)
                    sucesso = download_and_save_ai_image(prompt_otimizado, rel_path)
                    if sucesso:
                        novo_desafio.imagem = rel_path
                    else:
                        novo_desafio.imagem_url = generate_ai_image_url(prompt_otimizado)
                    novo_desafio.save()

                if ativar_imediatamente or Challenge.objects.filter(ativo=True).count() == 0:
                    novo_desafio.ativar()
                    messages.success(request, f"🎉 Desafio '{titulo}' cadastrado, com imagem gerada por IA e ATIVADO como a rodada atual do estande!")
                else:
                    messages.success(request, f"Desafio '{titulo}' salvo com imagem gerada por IA! Você pode ativá-lo quando quiser.")

                return redirect('game:operator_desafios')

        # 3. Ativar Rodada Selecionada
        elif action == 'activate_challenge':
            desafio_id = request.POST.get('challenge_id')
            desafio = get_object_or_404(Challenge, id=desafio_id)
            desafio.ativar()
            messages.success(request, f"🚀 Rodada {desafio.numero_rodada} ('{desafio.titulo}') ATIVADA! A tela das alunas foi atualizada.")
            return redirect('game:operator_desafios')

        # 4. Gerar / Regenerar Imagem por IA a partir do Prompt Cadastrado
        elif action == 'regenerate_image':
            desafio_id = request.POST.get('challenge_id')
            desafio = get_object_or_404(Challenge, id=desafio_id)
            import time
            rel_path = f"challenges/desafio_{desafio.id}_{int(time.time())}.jpg"
            prompt_otimizado = optimize_prompt_for_image_model(desafio.prompt_original)
            sucesso = download_and_save_ai_image(prompt_otimizado, rel_path)
            if sucesso:
                desafio.imagem = rel_path
                desafio.imagem_url = ""
                desafio.save()
                messages.success(request, f"🎨 Nova imagem gerada por IA com sucesso a partir do prompt para a Rodada {desafio.numero_rodada}!")
            else:
                desafio.imagem_url = generate_ai_image_url(prompt_otimizado)
                desafio.save()
                messages.warning(request, f"Imagem da IA configurada via URL direta para a Rodada {desafio.numero_rodada}.")
            return redirect('game:operator_desafios')

        # 5. Atualizar Dados / Prompt / Imagem de Desafio Existente
        elif action == 'update_challenge':
            desafio_id = request.POST.get('challenge_id')
            desafio = get_object_or_404(Challenge, id=desafio_id)
            desafio.titulo = request.POST.get('titulo', desafio.titulo).strip()
            desafio.numero_rodada = request.POST.get('numero_rodada', desafio.numero_rodada).strip()
            desafio.estilo_tag = request.POST.get('estilo_tag', desafio.estilo_tag).strip()
            
            novo_prompt = request.POST.get('prompt_original', desafio.prompt_original).strip()
            prompt_alterado = (novo_prompt != desafio.prompt_original)
            desafio.prompt_original = novo_prompt
            desafio.palavras_chave = request.POST.get('palavras_chave', desafio.palavras_chave).strip()
            desafio.dica_mascote = request.POST.get('dica_mascote', desafio.dica_mascote).strip()

            if 'imagem' in request.FILES:
                desafio.imagem = request.FILES['imagem']
                desafio.imagem_url = ""
            elif request.POST.get('imagem_url'):
                desafio.imagem_url = request.POST.get('imagem_url').strip()
            elif prompt_alterado or request.POST.get('gerar_nova_imagem_ia') == 'on':
                import time
                rel_path = f"challenges/desafio_{desafio.id}_{int(time.time())}.jpg"
                sucesso = download_and_save_ai_image(desafio.prompt_original, rel_path)
                if sucesso:
                    desafio.imagem = rel_path
                    desafio.imagem_url = ""
                else:
                    desafio.imagem_url = generate_ai_image_url(desafio.prompt_original)

            desafio.save()
            messages.success(request, f"✓ Desafio da Rodada {desafio.numero_rodada} atualizado com sucesso!")
            return redirect('game:operator_desafios')

        # 6. Excluir Desafio / Rodada
        elif action == 'delete_challenge':
            desafio_id = request.POST.get('challenge_id')
            desafio = get_object_or_404(Challenge, id=desafio_id)
            era_ativo = desafio.ativo
            titulo_deletado = desafio.titulo
            num_rodada = desafio.numero_rodada
            desafio.delete()

            # Se era o desafio ativo no estande, ativa o próximo disponível
            if era_ativo:
                restante = Challenge.objects.first()
                if restante:
                    restante.ativar()
                    messages.info(request, f"A Rodada {restante.numero_rodada} foi ativada automaticamente no estande.")

            messages.success(request, f"🗑️ Rodada {num_rodada} ('{titulo_deletado}') foi excluída com sucesso!")
            return redirect('game:operator_desafios')

    desafios = Challenge.objects.all().order_by('-ativo', '-id')
    desafio_ativo = Challenge.objects.filter(ativo=True).first()

    return render(request, 'game/operator_desafios.html', {
        'desafios': desafios,
        'desafio_ativo': desafio_ativo,
        'sugestao_gemini': sugestao_gemini,
    })

def operator_julgamento(request):
    """
    TELA 2 DO ADMIN / EQUIPE:
    Painel de Comparação e Julgamento.
    A equipe compara o prompt digitado pela aluna contra o prompt de referência salvo,
    avalia os cálculos de similaridade e define a vencedora/destaques da rodada.
    """
    if not check_equipe_permission(request):
        messages.warning(request, "Acesso restrito. Informe a senha de 6 dígitos para entrar no Modo Equipe.")
        return redirect('game:index')

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
            writer.writerow(['Posição', 'Participante', 'E-mail', 'Tentativa', 'Similaridade (%)', 'Decisão da Equipe', 'Prompt Digitado', 'Palavras Acertadas', 'Observação'])

            tentativas_csv = ParticipantAttempt.objects.filter(challenge=desafio_selecionado).order_by('-similaridade')
            for idx, att in enumerate(tentativas_csv, 1):
                writer.writerow([
                    idx,
                    att.nome_participante,
                    att.email_participante,
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



