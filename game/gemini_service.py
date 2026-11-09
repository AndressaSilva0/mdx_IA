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

def enhance_prompt_locally(prompt_pt: str) -> str:
    """
    Tradutor e enriquecedor semântico local de alta fidelidade para modelos de geração de imagem.
    Garante que o prompt em inglês seja descritivo, conceitualmente correto e ricamente estilizado,
    mesmo que a chave da API externa não esteja configurada ou atinja limites.
    """
    if not prompt_pt:
        return ""

    import re

    p = prompt_pt.lower().strip()

    # Dicionário de substituições e expansões semânticas direcionadas
    replacements = [
        (r'\bbarbie\b|\bboneca barbie\b', 'magical fairy fashion doll with iridescent crystalline butterfly wings, pastel pink and turquoise dress'),
        (r'\bboneca\b', 'exquisite collectible fairy doll, detailed clothing and sparkling accents'),
        (r'\bborboleta\b', 'delicate glowing bioluminescent butterfly wings'),
        (r'\bcachorro\b|\bcão\b|\bcãozinho\b|\bpet\b|\bgolden\b', 'adorable golden retriever dog wearing stylish kids denim overalls and colorful striped shirt'),
        (r'\bjardineira\b|\bjardineira jeans\b', 'kids denim overalls'),
        (r'\bshopping\b|\bshopping center\b', 'modern luxury shopping mall with polished reflective floors and soft warm lighting'),
        (r'\brobô\b|\brobo\b|\brobotica\b|\brobótica\b|\brover\b', 'autonomous high-tech robotic rover with glowing cyan lidar sensors'),
        (r'\blençóis maranhenses\b|\blencois maranhenses\b|\bdunas\b', 'pristine white sand dunes and crystal turquoise lagoons of Lencois Maranhenses under a twilight starry cosmic sky'),
        (r'\bafro\b|\bafrofuturismo\b', 'inspiring young Black woman scientist with stellar galactic afro hairstyle, programming floating neon holographic neural networks in a high-tech computer lab'),
        (r'\bcarro\b|\bcarro de corrida\b|\bcorrida\b', 'aerodynamic autonomous electric race car with glowing magenta LiDAR sensors speeding on an intelligent track'),
        (r'\bflor\b|\bflor mecânica\b|\bflor robotica\b', 'bioluminescent cybernetic mechanical glass flower with glowing fiber optic neon petals'),
        (r'\besfera\b|\besfera de cristal\b', 'transparent cosmic crystal orb floating in deep space with vibrant purple nebulae in background'),
        (r'\bmenina\b|\bjovem\b|\bcientista\b', 'young female STEM researcher scientist in futuristic tech vest'),
        (r'\bespacial\b|\bespaço\b', 'deep cosmic nebula with distant galaxies and twinkling stars'),
    ]

    expanded = p
    matched_any = False
    for pattern, repl in replacements:
        if re.search(pattern, expanded):
            expanded = re.sub(pattern, repl, expanded)
            matched_any = True

    # Modificadores de alta definição artística para evitar deformações anatômicas
    quality_modifiers = ", cinematic lighting, 8k resolution, sharp focus, masterpiece, highly detailed, award-winning digital concept art"

    if matched_any:
        return f"{expanded}{quality_modifiers}"
    else:
        # Se não casou com termos específicos, traduz elementos básicos e aplica reforço visual
        return f"cinematic digital art of {p}, vibrant colors, intricate details, volumetric lighting, 8k resolution, photorealistic render, sharp focus, masterpiece"

def optimize_prompt_for_image_model(prompt_pt: str) -> str:
    """
    Traduz e otimiza um prompt em português para um prompt visual em inglês de alta fidelidade
    para modelos de geração de imagem por IA, evitando desvios conceituais e baixa qualidade.
    """
    if not prompt_pt:
        return ""

    client = get_gemini_client()
    if client:
        instrucao = f"""
Translate and refine this Portuguese image description into an ultra-detailed, photorealistic visual prompt in English specifically tuned for high-end text-to-image AI models (like Flux.1 or SDXL).
Ensure subject details, species (e.g. dog vs human, doll vs plastic toy), materials, clothing, environment and lighting are vivid and clear so the AI generator produces a stunning, high-definition result.

Original Portuguese prompt:
"{prompt_pt}"

Output ONLY the refined English prompt string (max 45 words). No explanations, no markdown, no quotes.
"""
        try:
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=instrucao
            )
            if response and response.text:
                refined = response.text.strip().replace('"', '').replace("```", "")
                if refined:
                    return f"{refined}, 8k, cinematic lighting, masterpiece, sharp focus"
        except Exception as e:
            logger.warning(f"Gemini API indisponível ou chave inválida para otimizar prompt: {e}")

    # Fallback inteligente local
    return enhance_prompt_locally(prompt_pt)


