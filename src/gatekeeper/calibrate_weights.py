import json
import re
from collections import Counter

CORPUS_FILE = "data/autowein_full_corpus.jsonl"

def clean_and_tokenize(text):
    # Remove non-alphanumeric (keep spaces for n-grams)
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = text.split()
    return [w for w in words if len(w) > 1]

def get_ngrams(tokens, n):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def calibrate():
    print("Analyzing 10-Year Corpus for Key Themes (Bigrams)...")
    
    bigram_counts = Counter()
    total_docs = 0
    
    with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                # Combine Title + Comment (Comment reveals Autowein's specific focus/editorial angle)
                content = item.get('title', '') + " " + item.get('comment', '')
                tokens = clean_and_tokenize(content)
                
                # Extract Bigrams
                bigrams = get_ngrams(tokens, 2)
                bigram_counts.update(bigrams)
                total_docs += 1
            except: pass
            
    # Filter for meaningful phrases (appear in at least 0.1% of articles)
    threshold = total_docs * 0.001
    meaningful_phrases = {k: v for k, v in bigram_counts.items() if v > threshold}
    
    # Sort by frequency
    top_phrases = sorted(meaningful_phrases.items(), key=lambda x: x[1], reverse=True)[:50]
    
    print(f"\nTop 50 'Points' (Themes) Extracted from {total_docs} articles:")
    for phrase, count in top_phrases:
        print(f"- {phrase}: {count}")

if __name__ == "__main__":
    calibrate()
