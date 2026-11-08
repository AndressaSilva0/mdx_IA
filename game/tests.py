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

        # 1ª Tentativa
        response1 = self.client.post(url, {
            'action': 'submit_prompt',
            'nome_participante': nome,
            'prompt_enviado': 'Tentativa um flor no vidro'
        })
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(ParticipantAttempt.objects.filter(nome_participante=nome).count(), 1)

        # 2ª Tentativa
        response2 = self.client.post(url, {
            'action': 'submit_prompt',
            'nome_participante': nome,
            'prompt_enviado': 'Tentativa dois flor mecânica na esfera'
        })
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(ParticipantAttempt.objects.filter(nome_participante=nome).count(), 2)

        # 3ª Tentativa
        response3 = self.client.post(url, {
            'action': 'submit_prompt',
            'nome_participante': nome,
            'prompt_enviado': 'Tentativa tres flor mecânica esfera de cristal e espaço sideral'
        })
        self.assertEqual(response3.status_code, 302)
        self.assertEqual(ParticipantAttempt.objects.filter(nome_participante=nome).count(), 3)

        # 4ª Tentativa (deve ser bloqueada pois atingiu o limite de 3)
        response4 = self.client.post(url, {
            'action': 'submit_prompt',
            'nome_participante': nome,
            'prompt_enviado': 'Tentativa quatro que deve ser ignorada'
        })
        self.assertEqual(response4.status_code, 302)
        # O número total de tentativas continua sendo exatamente 3
        self.assertEqual(ParticipantAttempt.objects.filter(nome_participante=nome).count(), 3)

    def test_reset_session(self):
        # Seta aluna na sessão
        session = self.client.session
        session['current_participant'] = 'Larissa Mendes'
        session.save()

        reset_url = reverse('game:reset')
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('current_participant', self.client.session)

