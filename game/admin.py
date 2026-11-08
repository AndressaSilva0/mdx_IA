import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Challenge, ParticipantAttempt

@admin.action(description="Exportar tentativas selecionadas para CSV (Relatório do Evento)")
def export_attempts_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="mermas_digitais_tentativas_mdx2026.csv"'
    response.write(u'\ufeff'.encode('utf8'))  # BOM para compatibilidade com Microsoft Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'ID', 'Participante', 'Rodada', 'Desafio', 'Nº Tentativa',
        'Similaridade (%)', 'Palavras Acertadas', 'Prompt Enviado', 'Data/Hora'
    ])

    for attempt in queryset:
        writer.writerow([
            attempt.id,
            attempt.nome_participante,
            attempt.challenge.numero_rodada,
            attempt.challenge.titulo,
            attempt.numero_tentativa,
            f"{attempt.similaridade:.1f}",
            attempt.palavras_acertadas,
            attempt.prompt_enviado.replace('\n', ' '),
            attempt.data_envio.strftime('%d/%m/%Y %H:%M:%S')
        ])

    return response

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'numero_rodada', 'estilo_tag', 'ativo', 'criado_em')
    list_editable = ('ativo',)
    list_filter = ('ativo', 'numero_rodada')
    search_fields = ('titulo', 'prompt_original', 'palavras_chave', 'dica_mascote')
    fieldsets = (
        ('Identificação da Rodada', {
            'fields': ('titulo', 'numero_rodada', 'estilo_tag', 'ativo')
        }),
        ('Imagem de Inteligência Artificial', {
            'fields': ('imagem', 'imagem_url'),
            'description': 'Faça upload da imagem gerada por IA ou informe uma URL.'
        }),
        ('Prompt de Referência e Avaliação', {
            'fields': ('prompt_original', 'palavras_chave'),
            'description': 'Palavras-chave separadas por vírgula para cálculo de acertos.'
        }),
        ('Apoio Pedagógico da Mascote', {
            'fields': ('dica_mascote',),
            'description': 'Mensagem personalizada de incentivo e dicas para as participantes.'
        }),
    )

@admin.register(ParticipantAttempt)
class ParticipantAttemptAdmin(admin.ModelAdmin):
    list_display = ('nome_participante', 'challenge', 'numero_tentativa', 'similaridade_badge', 'data_envio')
    list_filter = ('challenge', 'numero_tentativa', 'data_envio')
    search_fields = ('nome_participante', 'prompt_enviado', 'palavras_acertadas')
    readonly_fields = ('data_envio',)
    ordering = ('-data_envio',)
    actions = [export_attempts_to_csv]

    @admin.display(description='Similaridade (%)', ordering='similaridade')
    def similaridade_badge(self, obj):
        return f"{obj.similaridade:.1f}%"


