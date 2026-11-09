"""
Serviço de Inteligência Artificial Google Gemini
Evento: Mermãs Digitais | MDX 2026 • IFMA
"""

import os
import logging
from google import genai
from google.genai import errors

logger = logging.getLogger(__name__)

# Modelo padrão de alta velocidade e precisão
DEFAULT_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite')

def get_gemini_client():
    """Inicializa o cliente do Google GenAI com a chave do .env."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Erro ao inicializar Google GenAI Client: {e}")
        return None

def generate_mascot_live_tip(nome_aluna: str, prompt_digitado: str, prompt_original: str, palavras_acertadas: list, similaridade: float, fallback_dica: str) -> str:
    """
    Gera uma dica pedagógica personalizada e empática da Mascote Mermãs
    usando o Google Gemini para apoiar a participante em sua próxima tentativa.
    """
    client = get_gemini_client()
    if not client or not prompt_digitado:
        return fallback_dica

    primeiro_nome = nome_aluna.split()[0].title() if nome_aluna else "Mermã"

    prompt_instrucao = f"""
Você é a carismática e inspiradora Mascote do projeto "Mermãs Digitais | MDX 2026 - IFMA" (iniciativa maranhense de meninas e mulheres na computação e inteligência artificial).
Uma estudante chamada {primeiro_nome} está no estande jogando para adivinhar o prompt de uma imagem gerada por IA.

DADOS DA TENTATIVA DELA:
- Prompt que a aluna digitou: "{prompt_digitado}"
- Pontuação alcançada: {similaridade:.1f}%
- Elementos que ela já acertou: {', '.join(palavras_acertadas) if palavras_acertadas else 'Nenhum elemento exato ainda'}
- Prompt de referência secreto: "{prompt_original}"

SUA MISSÃO:
Escreva uma dica de apoio curta (no máximo 2 frases), amigável, acolhedora e motivadora, direcionada a {primeiro_nome}.
1. Elogie a tentativa e destaque o que ela percebeu bem.
2. Dê uma pista sutil sobre cores, estilo ou ambiente que ela ainda não mencionou, sem revelar a resposta pronta.
3. Use tom alegre e empoderador.
"""

    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt_instrucao
        )
        if response and response.text:
            return response.text.strip().replace('"', '')
    except Exception as e:
        logger.warning(f"Falha na chamada ao Gemini, usando dica padrão: {e}")

    return fallback_dica

def generate_challenge_data_with_gemini(tema: str = "") -> dict:
    """
    Gera automaticamente uma nova rodada de desafio educativo com base no tema informado
    utilizando a inteligência artificial do Google Gemini.
    """
    client = get_gemini_client()
    if not client:
        return {}

    prompt_instrucao = f"""
Você é um especialista em educação STEM e inteligência artificial para o evento "Mermãs Digitais | MDX 2026 - IFMA".
Crie um novo desafio educativo onde as estudantes devem decodificar e adivinhar o prompt que gerou uma imagem por IA.
Tema sugerido pelo operador: "{tema if tema else 'Mulheres e meninas na robótica, computação e ciência no Maranhão'}"

Retorne estritamente um JSON no formato:
{{
  "titulo": "Título curto e instigante do desafio",
  "numero_rodada": "02",
  "estilo_tag": "Estilo da imagem (ex: Arte Digital Cyberpunk, Afrofuturismo, Fotografia Realista)",
  "prompt_original": "Descrição detalhada em português do Brasil e rica em elementos visuais da cena, iluminação e cores",
  "prompt_visual_en": "Detailed photorealistic visual prompt in English specifically optimized for text-to-image AI models describing the exact subject, action, clothing, environment, lighting and quality (e.g. 8k, sharp focus)",
  "palavras_chave": "4 a 6 termos cruciais separados por vírgula em português",
  "dica_mascote": "Dica pedagógica incentivando a aluna {{nome}} a focar nos detalhes mais marcantes"
}}
Apenas o JSON, sem markdown ou explicações.
"""

    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt_instrucao
        )
        if response and response.text:
            text = response.text.strip()
            # Limpa possíveis blocos ```json ... ```
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text.rsplit("\n", 1)[0]
            import json
            return json.loads(text.strip())
    except Exception as e:
        logger.warning(f"Erro ao gerar desafio com Gemini: {e}")

    return {}

def optimize_prompt_for_image_model(prompt_pt: str) -> str:
    """
    Traduz e otimiza um prompt em português para um prompt visual em inglês de alta fidelidade
    para modelos de geração de imagem por IA, evitando desvios conceituais (como humanos em vez de animais).
    """
    client = get_gemini_client()
    if not client or not prompt_pt:
        return prompt_pt

    instrucao = f"""
Translate and refine this Portuguese image description into an ultra-detailed, photorealistic visual prompt in English specifically tuned for text-to-image AI models (like Flux/Diffusion).
Ensure subject details, species (e.g. dog vs human), clothing, materials, environment and lighting are crystal clear so the AI generator produces an exact visual match.

Original Portuguese prompt:
"{prompt_pt}"

Output ONLY the refined English prompt string (max 40 words). No explanations, no quotes.
"""
    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=instrucao
        )
        if response and response.text:
            return response.text.strip().replace('"', '')
    except Exception as e:
        logger.warning(f"Erro ao otimizar prompt para imagem: {e}")

    return prompt_pt


