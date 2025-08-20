 
import tiktoken
import re


def clean_string_list(l):
    if isinstance(l, list):
        return [s.strip('"') for s in l if isinstance(s, str)]
    return l

def clean_milvus_results(raw_results: list) -> list:
        cleaned = []
        for result_group in raw_results:
            for item in result_group:
                try:
                    cleaned_item = {
                        "id": item.get("id"),
                        "score": float(item.get("distance")),
                        **item.get("entity", {})  # déstructure les champs de 'entity'
                    }
                    cleaned.append(cleaned_item)
                except Exception as e:
                    print("Erreur lors du nettoyage d'un item Milvus:", e)
        return cleaned

# un encoding proche de celui de ton modèle (ici on prend cl100k_base, très courant)
encoding = tiktoken.get_encoding("cl100k_base")

def split_into_chunks(text, max_tokens=500, overlap=100):
    # Étape 1 : découper en phrases
    sentences = re.split(r'(?<=[.?!])\s+', text.strip())
    
    chunks = []
    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        token_count = len(encoding.encode(sentence))

        # Si ajout de cette phrase dépasse max_tokens
        if current_tokens + token_count > max_tokens:
            chunk_text = " ".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
            
            # Overlap : on garde les dernières phrases
            overlap_tokens = 0
            overlap_chunk = []
            for s in reversed(current_chunk):
                s_tokens = len(encoding.encode(s))
                if overlap_tokens + s_tokens <= overlap:
                    overlap_chunk.insert(0, s)
                    overlap_tokens += s_tokens
                else:
                    break
            
            current_chunk = overlap_chunk.copy()
            current_tokens = sum(len(encoding.encode(s)) for s in current_chunk)

        # Ajouter la phrase en cours
        current_chunk.append(sentence)
        current_tokens += token_count

    # Ajouter le dernier chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks

