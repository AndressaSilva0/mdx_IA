"""
Módulo de cálculo de similaridade e processamento de linguagem natural
Evento: Mermãs Digitais | MDX 2026 • IFMA
"""

import difflib
import re
import unicodedata

# Stopwords comuns em Língua Portuguesa para filtrar ruídos na análise semântica
STOPWORDS_PT = {
    'a', 'ao', 'aos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aquilo', 'as', 'ate',
    'com', 'como', 'da', 'das', 'de', 'dela', 'delas', 'dele', 'deles', 'do', 'dos',
    'e', 'ela', 'elas', 'ele', 'eles', 'em', 'era', 'eram', 'essa', 'essas', 'esse',
    'esses', 'esta', 'estas', 'este', 'estes', 'eu', 'foi', 'fomos', 'foram', 'ha',
    'isso', 'isto', 'ja', 'lhe', 'lhes', 'mais', 'mas', 'me', 'mesmo', 'meu', 'meus',
    'minha', 'minhas', 'muito', 'na', 'nao', 'nas', 'nem', 'no', 'nos', 'nossa',
    'nossas', 'nosso', 'nossos', 'num', 'numa', 'o', 'os', 'ou', 'para', 'pela',
    'pelas', 'pelo', 'pelos', 'por', 'qual', 'quando', 'que', 'quem', 'se', 'seja',
    'sem', 'seu', 'seus', 'so', 'sua', 'suas', 'tambem', 'te', 'tem', 'ter', 'teu',
    'teus', 'tu', 'tua', 'tuas', 'um', 'uma', 'umas', 'uns', 'voce', 'voces'
}

def remove_accents(text: str) -> str:
    """Remove acentos ortográficos preservando as letras bases."""
    nfkd = unicodedata.normalize('NFKD', text)
    return u"".join([c for c in nfkd if not unicodedata.combining(c)])

def normalize_text(text: str) -> str:
    """Normaliza texto: minúsculas, sem acentos, sem pontuação excessiva."""
    if not text:
        return ""
    text = text.lower()
    text = remove_accents(text)
    # Remove pontuações e mantém apenas alfanuméricos e espaços
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_meaningful_tokens(text: str) -> set:
    """Extrai conjunto de palavras significativas ignorando stopwords."""
    norm = normalize_text(text)
    tokens = norm.split()
    return {w for w in tokens if w not in STOPWORDS_PT and len(w) > 2}

def find_matched_keywords(submitted_text: str, keywords_list: list) -> list:
    """
    Identifica quais palavras-chave do desafio a aluna acertou no prompt enviado.
    Suporta variações compostas e sinônimos separados por barra (ex: flor robótica/mecânica).
    """
    if not submitted_text or not keywords_list:
        return []

    norm_submitted = normalize_text(submitted_text)
    submitted_words = set(norm_submitted.split())
    matched = []

    for raw_kw in keywords_list:
        kw = raw_kw.strip()
        if not kw:
            continue

        # Verifica se há opções com barra (ex: "flor robótica/mecânica")
        sub_options = [opt.strip() for opt in kw.split('/')]
        hit = False

        for opt in sub_options:
            norm_opt = normalize_text(opt)
            # 1. Checa se a expressão exata está contida
            if norm_opt in norm_submitted:
                hit = True
                break
            
            # 2. Se for frase com várias palavras, checa se as palavras significativas estão no prompt
            opt_words = [w for w in norm_opt.split() if w not in STOPWORDS_PT and len(w) > 2]
            if opt_words and all(w in submitted_words or any(w in sw for sw in submitted_words) for w in opt_words):
                hit = True
                break

            # 3. Fuzzy match para digitações com pequenas variações
            for sw in submitted_words:
                if len(norm_opt) >= 4 and len(sw) >= 4:
                    if difflib.SequenceMatcher(None, norm_opt, sw).ratio() >= 0.85:
                        hit = True
                        break
            if hit:
                break

        if hit:
            matched.append(kw)

    return matched

def calculate_prompt_similarity(submitted_prompt: str, original_prompt: str, keywords_list: list) -> tuple:
    """
    Calcula a similaridade entre o prompt enviado e o original combinando:
    1. SequenceMatcher (ordem e estrutura textual)
    2. Interseção de Palavras-Chave essenciais (semântica do desafio)
    3. Sobreposição de tokens significativos (vocabulário em português)

    Retorna: (porcentagem_float_0_a_100, lista_de_palavras_acertadas)
    """
    if not submitted_prompt or not original_prompt:
        return 0.0, []

    norm_sub = normalize_text(submitted_prompt)
    norm_orig = normalize_text(original_prompt)

    # 1. Sequence Matcher estrutural
    seq_ratio = difflib.SequenceMatcher(None, norm_sub, norm_orig).ratio()

    # 2. Palavras-chave acertadas
    matched_kws = find_matched_keywords(submitted_prompt, keywords_list)
    total_kws = len(keywords_list)
    kw_ratio = (len(matched_kws) / total_kws) if total_kws > 0 else seq_ratio

    # 3. Sobreposição de vocabulário significativo (Jaccard ponderado)
    tokens_sub = extract_meaningful_tokens(submitted_prompt)
    tokens_orig = extract_meaningful_tokens(original_prompt)
    if tokens_orig:
        common_tokens = tokens_sub.intersection(tokens_orig)
        vocab_ratio = len(common_tokens) / len(tokens_orig)
    else:
        vocab_ratio = seq_ratio

    # Composição ponderada:
    # 45% acerto das palavras-chave conceituais da imagem
    # 30% vocabulário relevante utilizado
    # 25% similaridade sequencial do difflib
    raw_score = (0.45 * kw_ratio) + (0.30 * vocab_ratio) + (0.25 * seq_ratio)

    # Conversão para porcentagem
    score_pct = round(raw_score * 100, 1)

    # Limita entre 0% e 100%
    score_pct = max(0.0, min(100.0, score_pct))

    return score_pct, matched_kws

