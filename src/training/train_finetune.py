import json
import os
import sys
from typing import Dict, List, Optional
try:
    import torch
    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from trl import SFTTrainer
    HAS_LIB = True
except ImportError:
    HAS_LIB = False
    print("[Training] Transformers/TRL not found. Running in SIMULATION mode.")

CORPUS_FILE = "data/autowein_full_corpus.jsonl"
OUTPUT_DIR = "models/autowein_finetuned"
BASE_MODEL = "gpt2" # Placeholder for demo, replace with "meta-llama/Meta-Llama-3-8B-Instruct"

def load_data(file_path: str) -> List[Dict]:
    data = []
    if not os.path.exists(file_path):
        print(f"Corpus file not found: {file_path}")
        return []
        
    print(f"Loading data from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                # Filter for items with BOTH text and comment
                if item.get('text') and item.get('comment'):
                    # Create instruction format
                    data.append({
                        "instruction": "Analyze the following automotive news article and provide expert commentary.",
                        "input": item['text'],
                        "output": item['comment']
                    })
            except: pass
    return data

def format_prompt(sample):
    """
    Format the data for the model (Llama-3 style or generic).
    """
    return f"""### System:
You are an expert automotive analyst for Autowein. Provide sharp, context-aware commentary on the news.

### User:
{sample['input']}

### Assistant:
{sample['output']}
"""

def main():
    print(f"[Training] Starting Fine-tuning Pipeline...")
    
    raw_data = load_data(CORPUS_FILE)
    print(f"[Training] Loaded {len(raw_data)} valid training pairs (Text -> Comment).")
    
    if len(raw_data) == 0:
        print("[Training] No data found. Please wait for crawler to finish or check file path.")
        return

    # Simulation Mode
    if not HAS_LIB or not torch.cuda.is_available():
        print("[Training] Simulating Training Process (CPU/No-Lib Mode)...")
        import time
        max_steps = 5
        for i in range(max_steps):
            time.sleep(0.2)
            loss = 2.5 - (i * 0.4)
            print(f"Step {i+1}/{max_steps} | Loss: {loss:.4f}")
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(OUTPUT_DIR, "adapter_config.json"), "w") as f:
            f.write(json.dumps({"base_model": BASE_MODEL, "steps": max_steps}))
            
        print(f"[Training] Training finished (Simulated). Model saved to {OUTPUT_DIR}")
        return

    # Real Training Mode
    print(f"[Training] GPU Detected: {torch.cuda.get_device_name(0)}")
    dataset = Dataset.from_list(raw_data)
    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token
    
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        report_to="none"
    )
    
    trainer = SFTTrainer(
        model=BASE_MODEL,
        train_dataset=dataset,
        dataset_text_field="input", # formatting_func handles structure
        formatting_func=format_prompt,
        args=args,
    )
    
    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    print(f"[Training] Model saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
