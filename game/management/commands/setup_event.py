from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from game.models import Challenge, ParticipantAttempt
from django.utils import timezone

class Command(BaseCommand):
    help = 'Cria o operador administrativo e o Desafio Inicial da Rodada 01 para o estande MDX 2026'

    def handle(self, *args, **options):
        User = get_user_model()

        # 1. Cria usuário Operador / Administrador
        username = 'operador'
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email='mermas@ifma.edu.br',
                password='mermas2026ifma'
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Superusuário '{username}' criado com sucesso! (Senha: mermas2026ifma)"))
        else:
            self.stdout.write(self.style.WARNING(f"Usuário '{username}' já existe."))

        # 2. Cria Desafio Inicial conforme o Mockup Oficial do Evento
        challenge, created = Challenge.objects.get_or_create(
            numero_rodada='01',
            defaults={
                'titulo': 'Flor Mecânica em Esfera de Cristal Cósmica',
                'estilo_tag': 'Estilo Mágico & Futurista',
                'imagem': 'challenges/flor_cristal.jpg',
                'prompt_original': (
                    "Arte digital colorida e surrealista de uma flor mecânica cibernética "
                    "brilhando com filamentos de luz neon dentro de uma esfera de cristal transparente, "
                    "flutuando no espaço sideral escuro com pequenas estrelas."
                ),
                'dica_mascote': (
                    "Oi, {nome}! Olhe com atenção os detalhes da imagem: a esfera de cristal transparente, "
                    "a flor robótica bioluminescente e o fundo escuro sideral. "
                    "Refine as palavras-chave no seu próximo prompt!"
                ),
                'palavras_chave': 'esfera de cristal, flor robótica/mecânica, brilho bioluminescente, espaço sideral',
                'ativo': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS("✓ Desafio Inicial da Rodada 01 cadastrado e ativado!"))
        else:
            challenge.ativo = True
            challenge.save()
            self.stdout.write(self.style.SUCCESS("✓ Desafio Inicial da Rodada 01 já existente e garantido ativo."))

        # 3. Cria uma participante de exemplo para demonstrar o visual idêntico ao mockup
        if not ParticipantAttempt.objects.filter(nome_participante='Camila Ferreira Santos').exists():
            ParticipantAttempt.objects.create(
                challenge=challenge,
                nome_participante='Camila Ferreira Santos',
                numero_tentativa=1,
                prompt_enviado='Flor de vidro brilhando no espaço com detalhes roxos e azuis no fundo escuro...',
                similaridade=74.2,
                palavras_acertadas='esfera de cristal, espaço sideral',
                data_envio=timezone.now()
            )
            ParticipantAttempt.objects.create(
                challenge=challenge,
                nome_participante='Camila Ferreira Santos',
                numero_tentativa=2,
                prompt_enviado=(
                    "Arte digital colorida e surrealista de uma flor mecânica cibernética brilhando "
                    "com filamentos de luz neon dentro de uma esfera de cristal transparente, "
                    "flutuando no espaço sideral escuro com pequenas estrelas."
                ),
                similaridade=88.5,
                palavras_acertadas='esfera de cristal, flor robótica/mecânica, brilho bioluminescente, espaço sideral',
                data_envio=timezone.now()
            )
            self.stdout.write(self.style.SUCCESS("✓ Tentativas de exemplo da aluna 'Camila Ferreira Santos' criadas com sucesso."))

        self.stdout.write(self.style.SUCCESS("\n🎉 Ambiente do Jogo MDX 2026 configurado e pronto para o estande!"))

