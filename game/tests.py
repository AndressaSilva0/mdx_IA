from django.test import TestCase, Client
from django.urls import reverse
from game.models import Challenge, ParticipantAttempt
from game.utils import calculate_prompt_similarity, normalize_text, find_matched_keywords

class MDXGameTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.challenge = Challenge.objects.create(
            titulo='Esfera Cósmica',
            numero_rodada='01',
            estilo_tag='Estilo Mágico & Futurista',
            prompt_original='Flor mecânica cibernética brilhando dentro de uma esfera de cristal flutuando no espaço sideral.',
            dica_mascote='Oi, {nome}! Olhe com atenção os detalhes da esfera de cristal e espaço sideral.',
            palavras_chave='esfera de cristal, flor mecânica, espaço sideral, brilhando',
            ativo=True
        )

    def test_normalize_text(self):
        text = "Robótica & Flor Elétrica, no Espaço!"
        normalized = normalize_text(text)
        self.assertEqual(normalized, "robotica flor eletrica no espaco")

    def test_matched_keywords(self):
        kws = ['esfera de cristal', 'flor mecânica/robótica', 'espaço sideral']
        submitted = "Eu acho que é uma flor mecânica dentro de uma esfera de cristal bonita"
        matched = find_matched_keywords(submitted, kws)
        self.assertIn('esfera de cristal', matched)
        self.assertIn('flor mecânica/robótica', matched)
        self.assertNotIn('espaço sideral', matched)

    def test_calculate_similarity_accuracy(self):
        kws = ['esfera de cristal', 'flor mecânica', 'espaço sideral']
        orig = "Flor mecânica dentro de esfera de cristal no espaço sideral"
        
        # Teste 1: Texto idêntico deve ser 100%
        score_full, matched_full = calculate_prompt_similarity(orig, orig, kws)
        self.assertEqual(score_full, 100.0)
        self.assertEqual(len(matched_full), 3)

        # Teste 2: Texto parcial
        partial = "Uma flor mecânica flutuando pelo espaço sideral"
        score_part, matched_part = calculate_prompt_similarity(partial, orig, kws)
        self.assertTrue(50.0 <= score_part <= 90.0)

    def test_participant_3_attempts_flow(self):
        url = reverse('game:index')
        nome = "Ana Beatriz"
        email = "ana.beatriz@ifma.edu.br"

        # 1ª Tentativa
        response1 = self.client.post(url, {
            'action': 'submit_prompt',
            'nome_participante': nome,
            'email_participante': email,
            'prompt_enviado': 'Tentativa um flor no vidro'
        })
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(ParticipantAttempt.objects.filter(email_participante=email).count(), 1)

        # 2ª Tentativa
        response2 = self.client.post(url, {
            'action': 'submit_prompt',
            'nome_participante': nome,
            'email_participante': email,
            'prompt_enviado': 'Tentativa dois flor mecânica na esfera'
        })
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(ParticipantAttempt.objects.filter(email_participante=email).count(), 2)

        # 3ª Tentativa
        response3 = self.client.post(url, {
            'action': 'submit_prompt',
            'nome_participante': nome,
            'email_participante': email,
            'prompt_enviado': 'Tentativa tres flor mecânica esfera de cristal e espaço sideral'
        })
        self.assertEqual(response3.status_code, 302)
        self.assertEqual(ParticipantAttempt.objects.filter(email_participante=email).count(), 3)

        # 4ª Tentativa (deve ser bloqueada pois atingiu o limite de 3)
        response4 = self.client.post(url, {
            'action': 'submit_prompt',
            'nome_participante': nome,
            'email_participante': email,
            'prompt_enviado': 'Tentativa quatro que deve ser ignorada'
        })
        self.assertEqual(response4.status_code, 302)
        # O número total de tentativas continua sendo exatamente 3
        self.assertEqual(ParticipantAttempt.objects.filter(email_participante=email).count(), 3)

    def test_pin_6_digitos_modalidade_switch(self):
        url_pin = reverse('game:trocar_modalidade_equipe')
        
        # Teste 1: PIN Errado
        res_errado = self.client.post(url_pin, {'pin': '000000'}, follow=True)
        self.assertEqual(res_errado.status_code, 200)
        self.assertFalse(self.client.session.get('is_equipe'))

        # Teste 2: PIN Correto de 6 dígitos (262026)
        res_correto = self.client.post(url_pin, {'pin': '262026'}, follow=True)
        self.assertEqual(res_correto.status_code, 200)
        self.assertTrue(self.client.session.get('is_equipe'))

        # Teste 3: Sair da modalidade equipe
        url_sair = reverse('game:sair_modalidade_equipe')
        res_sair = self.client.get(url_sair, follow=True)
        self.assertEqual(res_sair.status_code, 200)
        self.assertFalse(self.client.session.get('is_equipe'))

    def test_reset_session(self):
        # Seta aluna na sessão
        session = self.client.session
        session['current_participant'] = 'Larissa Mendes'
        session.save()

        reset_url = reverse('game:reset')
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('current_participant', self.client.session)

    def test_api_rodada_ativa(self):
        url = reverse('game:api_rodada_ativa')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ativo'])
        self.assertEqual(data['id'], self.challenge.id)

    def test_operator_flow(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='testoperador', password='password123')
        self.client.login(username='testoperador', password='password123')

        # Cria nova rodada 02
        url_desafios = reverse('game:operator_desafios')
        res_create = self.client.post(url_desafios, {
            'action': 'create_challenge',
            'titulo': 'Rodada Nova 02',
            'numero_rodada': '02',
            'estilo_tag': 'Cyberpunk',
            'prompt_original': 'Robô espacial em Marte',
            'palavras_chave': 'robô, marte, espacial',
            'dica_mascote': 'Dica teste',
            'ativar_imediatamente': 'on'
        })
        self.assertEqual(res_create.status_code, 302)
        
        # A Rodada 02 agora é a ativa
        c2 = Challenge.objects.get(numero_rodada='02')
        self.assertTrue(c2.ativo)
        self.challenge.refresh_from_db()
        self.assertFalse(self.challenge.ativo)

        # Julgamento
        att = ParticipantAttempt.objects.create(
            challenge=c2,
            nome_participante='Juliana Teste',
            numero_tentativa=1,
            prompt_enviado='robô espacial',
            similaridade=90.0,
            palavras_acertadas='robô, espacial'
        )
        url_julg = reverse('game:operator_julgamento')
        res_decisao = self.client.post(url_julg, {
            'action': 'decidir_vencedor',
            'attempt_id': att.id,
            'decisao': 'vencedora',
            'observacao': 'Excelente prompt!'
        })
        self.assertEqual(res_decisao.status_code, 302)
        att.refresh_from_db()
        self.assertEqual(att.decisao_equipe, 'vencedora')
        self.assertEqual(att.observacao_equipe, 'Excelente prompt!')

    def test_save_participant_action(self):
        url = reverse('game:index')
        nome = "Camila Ferreira"
        email = "camila.ferreira@ifma.edu.br"

        # Aluna salva o participante antes de enviar o prompt
        response = self.client.post(url, {
            'action': 'save_participant',
            'nome_participante': nome,
            'email_participante': email,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get('current_participant'), nome)
        self.assertEqual(self.client.session.get('current_email'), email)

    def test_ranking_best_score_and_top3_prizes(self):
        from game.views import get_challenge_ranking

        # Aluna A: 3 tentativas (scores: 50.0, 92.0, 70.0) -> melhor: 92.0
        ParticipantAttempt.objects.create(
            challenge=self.challenge,
            nome_participante='Aluna A',
            email_participante='aluna.a@ifma.edu.br',
            numero_tentativa=1,
            prompt_enviado='prompt 1',
            similaridade=50.0
        )
        ParticipantAttempt.objects.create(
            challenge=self.challenge,
            nome_participante='Aluna A',
            email_participante='aluna.a@ifma.edu.br',
            numero_tentativa=2,
            prompt_enviado='prompt 2',
            similaridade=92.0
        )
        ParticipantAttempt.objects.create(
            challenge=self.challenge,
            nome_participante='Aluna A',
            email_participante='aluna.a@ifma.edu.br',
            numero_tentativa=3,
            prompt_enviado='prompt 3',
            similaridade=70.0
        )

        # Aluna B: 2 tentativas (scores: 85.0, 88.0) -> melhor: 88.0
        ParticipantAttempt.objects.create(
            challenge=self.challenge,
            nome_participante='Aluna B',
            email_participante='aluna.b@ifma.edu.br',
            numero_tentativa=1,
            prompt_enviado='prompt 1',
            similaridade=85.0
        )
        ParticipantAttempt.objects.create(
            challenge=self.challenge,
            nome_participante='Aluna B',
            email_participante='aluna.b@ifma.edu.br',
            numero_tentativa=2,
            prompt_enviado='prompt 2',
            similaridade=88.0
        )

        # Aluna C: 1 tentativa (score: 75.0) -> melhor: 75.0
        ParticipantAttempt.objects.create(
            challenge=self.challenge,
            nome_participante='Aluna C',
            email_participante='aluna.c@ifma.edu.br',
            numero_tentativa=1,
            prompt_enviado='prompt 1',
            similaridade=75.0
        )

        # Aluna D: 1 tentativa (score: 60.0) -> melhor: 60.0 (4º lugar, fora do Top 3)
        ParticipantAttempt.objects.create(
            challenge=self.challenge,
            nome_participante='Aluna D',
            email_participante='aluna.d@ifma.edu.br',
            numero_tentativa=1,
            prompt_enviado='prompt 1',
            similaridade=60.0
        )

        ranking = get_challenge_ranking(self.challenge)
        self.assertEqual(len(ranking), 4)

        # 1º Lugar (Ouro)
        self.assertEqual(ranking[0]['nome'], 'Aluna A')
        self.assertEqual(ranking[0]['melhor_score'], 92.0)
        self.assertEqual(ranking[0]['posicao'], 1)
        self.assertTrue(ranking[0]['is_top3'])
        self.assertIn('Ouro', ranking[0]['premio_label'])

        # 2º Lugar (Prata)
        self.assertEqual(ranking[1]['nome'], 'Aluna B')
        self.assertEqual(ranking[1]['melhor_score'], 88.0)
        self.assertEqual(ranking[1]['posicao'], 2)
        self.assertTrue(ranking[1]['is_top3'])
        self.assertIn('Prata', ranking[1]['premio_label'])

        # 3º Lugar (Bronze)
        self.assertEqual(ranking[2]['nome'], 'Aluna C')
        self.assertEqual(ranking[2]['melhor_score'], 75.0)
        self.assertEqual(ranking[2]['posicao'], 3)
        self.assertTrue(ranking[2]['is_top3'])
        self.assertIn('Bronze', ranking[2]['premio_label'])

        # 4º Lugar (Fora do Top 3 de premiação)
        self.assertEqual(ranking[3]['nome'], 'Aluna D')
        self.assertEqual(ranking[3]['melhor_score'], 60.0)
        self.assertEqual(ranking[3]['posicao'], 4)
        self.assertFalse(ranking[3]['is_top3'])
        self.assertEqual(ranking[3]['premio_label'], 'Classificada')

        # Testa renderização do ranking no leaderboard
        url_rank = reverse('game:ranking')
        res_rank = self.client.get(url_rank)
        self.assertEqual(res_rank.status_code, 200)
        self.assertContains(res_rank, 'Aluna A')
        self.assertContains(res_rank, '92.0%')
        self.assertContains(res_rank, '1º Lugar (Prêmio Ouro)')

    def test_delete_challenge(self):
        c = Challenge.objects.create(
            titulo='Desafio para Excluir',
            numero_rodada='99',
            prompt_original='prompt teste',
            palavras_chave='teste',
            ativo=False
        )
        self.assertEqual(Challenge.objects.filter(id=c.id).count(), 1)

        session = self.client.session
        session['is_equipe'] = True
        session.save()

        url_desafios = reverse('game:operator_desafios')
        res = self.client.post(url_desafios, {
            'action': 'delete_challenge',
            'challenge_id': c.id
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Challenge.objects.filter(id=c.id).count(), 0)


