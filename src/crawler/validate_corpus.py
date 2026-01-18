import json
import os

INPUT_FILE = "data/autowein_full_corpus.jsonl"
TEMP_FILE = "data/autowein_full_corpus_clean.jsonl"

def clean_corpus():
    valid_count = 0
    corrupt_count = 0
    
    if not os.path.exists(INPUT_FILE):
        print(f"File not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
         open(TEMP_FILE, 'w', encoding='utf-8') as fout:
        
        for i, line in enumerate(fin):
            line = line.strip()
            if not line: continue
            
            try:
                # Try simple parse
                obj = json.loads(line)
                # Check critical fields
                if 'id' in obj and 'text' in obj:
                    fout.write(json.dumps(obj, ensure_ascii=False) + '\n')
                    valid_count += 1
                else:
                    print(f"Skipping line {i+1}: Missing critical fields")
                    corrupt_count += 1
            except json.JSONDecodeError:
                # Attempt recovering if it's a concatenation issue
                # e.g. {...}{...}
                print(f"Corrupt JSON at line {i+1}. Attempting recovery...")
                try:
                    # Simple heuristic: Split by '}{'
                    parts = line.replace('}{', '}\n{').split('\n')
                    for p in parts:
                        obj = json.loads(p)
                        fout.write(json.dumps(obj, ensure_ascii=False) + '\n')
                        valid_count += 1
                        print(f" -> Recovered item from line {i+1}")
                except:
                    print(f" -> Failed to recover line {i+1}")
                    corrupt_count += 1
                    
    print(f"Done. Valid: {valid_count}, Corrupt/Fixed: {corrupt_count}")
    # Replace original
    os.replace(TEMP_FILE, INPUT_FILE)

if __name__ == "__main__":
    clean_corpus()
