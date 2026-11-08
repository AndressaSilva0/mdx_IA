from django.db import models
from django.utils import timezone

class Challenge(models.Model):
    """
    Representa a rodada e a imagem gerada por IA que as alunas tentarão adivinhar o prompt.
    """
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título da Rodada / Desafio",
        help_text="Ex: Flor Cibernética em Vidro Sideral"
    )
    numero_rodada = models.CharField(
        max_length=50,
        default="01",
        verbose_name="Número/Identificador da Rodada",
        help_text="Ex: 01, 02 ou Rodada 01: Decodificação Criativa"
    )
    estilo_tag = models.CharField(
        max_length=100,
        default="Estilo Mágico & Futurista",
        verbose_name="Tag de Estilo da Imagem",
        help_text="Ex: Estilo Mágico & Futurista, Cyberpunk, Arte Vetorial 2D"
    )
    imagem = models.ImageField(
        upload_to='challenges/',
        blank=True,
        null=True,
        verbose_name="Arquivo da Imagem de IA"
    )
    imagem_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL alternativa da Imagem (caso não use upload)"
    )
    prompt_original = models.TextField(
        verbose_name="Prompt Original de Referência",
        help_text="O prompt exato utilizado para gerar a imagem na IA."
    )
    dica_mascote = models.TextField(
        verbose_name="Dica da Mascote Mermãs",
        help_text="Dica pedagógica que a mascote dará para apoiar a participante."
    )
    palavras_chave = models.CharField(
        max_length=500,
        verbose_name="Palavras-Chave de Avaliação",
        help_text="Termos cruciais separados por vírgula. Ex: esfera de cristal, flor robótica, bioluminescente, espaço sideral"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Desafio Ativo para o Estande?",
        help_text="Apenas o desafio ativo será exibido na tela do jogo."
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Desafio / Rodada"
        verbose_name_plural = "Desafios / Rodadas"
        ordering = ['-ativo', '-id']

    def __str__(self):
        status = " [ATIVO]" if self.ativo else ""
        return f"Rodada {self.numero_rodada}: {self.titulo}{status}"

    @property
    def get_image_url(self):
        if self.imagem:
            return self.imagem.url
        if self.imagem_url:
            return self.imagem_url
        return "/static/game/img/ai_sample.jpg"

    def get_palavras_chave_list(self):
        """Retorna lista de palavras-chave limpas e sem espaços extras."""
        if not self.palavras_chave:
            return []
        return [p.strip() for p in self.palavras_chave.split(',') if p.strip()]

    def ativar(self):
        """Ativa este desafio como o atual do estande e desativa todos os outros."""
        Challenge.objects.exclude(id=self.id).update(ativo=False)
        self.ativo = True
        self.save(update_fields=['ativo'])


class ParticipantAttempt(models.Model):
    """
    Registra cada uma das 3 tentativas feitas por cada participante em um desafio.
    """
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="Desafio da Rodada"
    )
    nome_participante = models.CharField(
        max_length=150,
        verbose_name="Nome Completo da Participante",
        db_index=True
    )
    numero_tentativa = models.IntegerField(
        verbose_name="Número da Tentativa (1 a 3)",
        choices=[(1, '1ª Tentativa'), (2, '2ª Tentativa'), (3, '3ª Tentativa')]
    )
    prompt_enviado = models.TextField(
        verbose_name="Prompt Digitado pela Participante"
    )
    similaridade = models.FloatField(
        verbose_name="Porcentagem de Similaridade (0 a 100%)",
        help_text="Calculado pela combinação de SequenceMatcher e interseção de palavras-chave"
    )
    palavras_acertadas = models.TextField(
        blank=True,
        default="",
        verbose_name="Palavras-Chave Acertadas",
        help_text="Lista de palavras-chave detectadas no prompt enviado (separadas por vírgula)"
    )
    data_envio = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data e Hora do Envio"
    )

    STATUS_DECISAO = [
        ('pendente', 'Em Avaliação'),
        ('vencedora', 'Vencedora da Rodada 🏆'),
        ('destaque', 'Destaque Criativo ✨'),
        ('homologada', 'Classificada'),
    ]
    decisao_equipe = models.CharField(
        max_length=50,
        choices=STATUS_DECISAO,
        default='pendente',
        verbose_name="Decisão da Equipe"
    )
    observacao_equipe = models.TextField(
        blank=True,
        default="",
        verbose_name="Observação / Parecer da Equipe"
    )

    class Meta:
        verbose_name = "Tentativa de Participante"
        verbose_name_plural = "Tentativas das Participantes"
        ordering = ['challenge', 'nome_participante', 'numero_tentativa']

    def __str__(self):
        return f"{self.nome_participante} - Rodada {self.challenge.numero_rodada} - Tentativa {self.numero_tentativa} ({self.similaridade:.1f}%)"

    def get_palavras_acertadas_list(self):
        if not self.palavras_acertadas:
            return []
        return [p.strip() for p in self.palavras_acertadas.split(',') if p.strip()]

