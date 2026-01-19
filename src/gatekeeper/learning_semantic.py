import json
import joblib
import numpy as np
import os
from sklearn.svm import OneClassSVM
from sentence_transformers import SentenceTransformer

CORPUS_FILE = "data/autowein_full_corpus.jsonl"
MODEL_FILE = "data/semantic_model.pkl"
# Switched to Multilingual Model (Support for KR, JP, CN, US)
EMBEDDER_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

def train_semantic_model():
    print(f"[Deep IRL] Training Semantic One-Class SVM on {CORPUS_FILE}...")
    
    # 1. Load Data
    texts = []
    try:
        with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    # Combine Title + Comment for rich context
                    # If 'comment' is missing, fallback to content snippet or just title
                    # Autowein 'style' is often in the title + the analyst's comment
                    combined = item.get('title', '') + " " + item.get('comment', '')
                    if len(combined) > 10:
                        texts.append(combined)
                except: pass
    except FileNotFoundError:
        print("Corpus not found.")
        return

    # Optimization: Sample 3000 items to speed up CPU training (Full 23k takes too long without GPU)
    # BUT: Learn Reputation from ALL items first!
    
    print("[Deep IRL] Learning Source Reputation from FULL History (23k)...")
    from urllib.parse import urlparse
    from collections import Counter
    
    domain_counts = Counter()
    # Read full file for reputation
    try:
        with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    url = item.get('url', '')
                    if url:
                        # Logic must match Engine exactly
                        domain = urlparse(url).netloc.replace('www.', '')
                        domain_counts[domain] += 1
                except: pass
    except: pass
    print(f"[Deep IRL] Identified {len(domain_counts)} trusted domains.")

    # Now subsample for SVM
    import random
    if len(texts) > 3000:
        print("[Deep IRL] Subsampling 3,000 items for SVM training...")
        texts = random.sample(texts, 3000)
    
    # 2. Embed (Vectorize)
    # Load SBERT
    print(f"[Deep IRL] Loading SBERT: {EMBEDDER_NAME}...")
    embedder = SentenceTransformer(EMBEDDER_NAME, device='cpu')
    
    print("[Deep IRL] Embedding corpus (this may take a moment)...")
    embeddings = embedder.encode(texts, batch_size=64, show_progress_bar=True)
    
    # 3. Train One-Class SVM
    # Refinement: nu=0.1 (Reverting to 10% outlier assumption for broader acceptance)
    print("[Deep IRL] Fitting One-Class SVM (nu=0.1)...")
    clf = OneClassSVM(nu=0.1, kernel="rbf", gamma="scale")
    clf.fit(embeddings)
    
    # 3.5 Reputation already learned globally above
    
    # 4. Save
    model_data = {
        "svm": clf,
        "embedder_name": EMBEDDER_NAME,
        "trusted_domains": dict(domain_counts) # Save trusted list from FULL corpus
    }
    
    joblib.dump(model_data, MODEL_FILE)
    print(f"[Deep IRL] Saved Semantic & Reputation Model to {MODEL_FILE}")

if __name__ == "__main__":
    train_semantic_model()
