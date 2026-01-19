import json
import math
import re
from collections import Counter
from typing import Dict

CORPUS_FILE = "data/autowein_full_corpus.jsonl"
MODEL_FILE = "data/irl_tfidf_model.json"

def clean_text(text: str) -> list[str]:
    # Simple tokenizer retaining some semantic meaning
    text = re.sub(r'[^\w\s]', '', text.lower())
    return [w for w in text.split() if len(w) > 1 and not w.isdigit()]

def train_tfidf_model():
    print(f"[Deep IRL] Training TF-IDF Model on {CORPUS_FILE}...")
    
    # 1. Document Frequency (DF)
    # How many documents does each word appear in?
    doc_freq = Counter()
    total_docs = 0
    
    try:
        with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    # Combine title context
                    text = item.get('title', '') + " " + item.get('comment', '')
                    unique_tokens = set(clean_text(text))
                    
                    doc_freq.update(unique_tokens)
                    total_docs += 1
                except: pass
    except FileNotFoundError:
        print("Corpus not found. Using dummy model.")
    
    print(f"[Deep IRL] Analyzed {total_docs} documents. Vocab size: {len(doc_freq)}")
    
    # 2. Calculate IDF (Inverse Document Frequency)
    # IDF(w) = log( (N / (df + 1)) )
    # Words appearing in ALL docs (df ~ N) get score ~ 0.
    # Words appearing in FEW docs get score > 0.
    
    idf_scores = {}
    for word, df in doc_freq.items():
        # Filter: Remove extremely rare words (noise)
        if df < 3: continue 
        
        idf = math.log(total_docs / (df + 1))
        idf_scores[word] = idf
        
    # Heuristic: Boost words that look like 'tech' or 'biz' terms (optional, simple logic)
    # or just rely on math. Math is usually enough.
        
    model_data = {
        "idf_scores": idf_scores,
        "default_idf": 0.0, # Unknown words contribute 0
        "total_docs": total_docs
    }
    
    with open(MODEL_FILE, 'w', encoding='utf-8') as f:
        json.dump(model_data, f, ensure_ascii=False)
        
    print(f"[Deep IRL] Saved 'TF-IDF Weight Model' to {MODEL_FILE}")

if __name__ == "__main__":
    train_tfidf_model()
