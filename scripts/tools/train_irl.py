import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import random

# Configuration
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
WEIGHTS_PATH = "data/irl_weights.pth"
BATCH_SIZE = 16
EPOCHS = 5

class PreferenceDataset(Dataset):
    def __init__(self, positives: List[str], negatives: List[str], embedder):
        self.data = []
        self.embedder = embedder
        
        # Pre-embed or embed on fly? Embed on fly is slower but saves RAM.
        # Let's pre-embed for small datasets.
        print("[Trainer] Embedding data...")
        pos_embs = embedder.encode(positives, convert_to_tensor=True)
        neg_embs = embedder.encode(negatives, convert_to_tensor=True)
        
        for emb in pos_embs:
            self.data.append((emb, 1.0)) # Label 1.0 for selected
        for emb in neg_embs:
            self.data.append((emb, 0.0)) # Label 0.0 for ignored
            
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]

def train_irl_head():
    """
    Trains the Linear Classification Head on user-curated data.
    Input: '2_curated.json' files (Positives) and '1_selected_ranked.json' (Negatives = Selected - Curated).
    """
    import glob
    import json
    
    print("=== [IRL Trainer] Starting Preference Learning ===")
    
    positives = []
    negatives = []
    
    # 1. Scan Data Directory for User Feedback
    # We look for '2_curated.json' (Positives) and '1_selected_ranked.json' (The Pool)
    # Negatives = Pool - Positives
    daily_dirs = glob.glob("data/daily/*")
    print(f"[Trainer] Scanning {len(daily_dirs)} daily logs...")
    
    for d_dir in daily_dirs:
        curated_path = os.path.join(d_dir, "2_curated.json")
        selected_path = os.path.join(d_dir, "1_selected_ranked.json")
        
        if os.path.exists(curated_path) and os.path.exists(selected_path):
            try:
                with open(curated_path, 'r') as f:
                    curated_items = json.load(f)
                    pos_ids = {item['id'] for item in curated_items}
                    for item in curated_items:
                        # Training on Title + Content snippet
                        text = f"{item['title']} {item['content'][:200]}"
                        positives.append(text)
                        
                with open(selected_path, 'r') as f:
                    all_items = json.load(f)
                    for item in all_items:
                        if item['id'] not in pos_ids:
                            # If it was in the pool but NOT selected by user -> Implicit Negative
                            text = f"{item['title']} {item['content'][:200]}"
                            negatives.append(text)
            except Exception as e:
                print(f"[Trainer] Error reading {d_dir}: {e}")

    # Fallback to Mock Data if no history yet (Cold Start)
    if not positives:
        print("[Trainer] No historical user choices found. Using Cold-Start Mock Data.")
        positives = [
            "Tesla releases new Optimus Gen 2 robot",
            "Ford cuts F-150 Lightning production due to demand",
            "BYD overtakes Volkswagen in China sales",
            "CATL announces solid-state battery breakthrough"
        ]
        negatives = [
            "10 best stocks to buy now - Motley Fool",
            "Why this penny stock is soaring",
            "Top 5 dashcams for your car",
            "Generic press release about a local dealership award"
        ]
    else:
        print(f"[Trainer] Loaded {len(positives)} Positives and {len(negatives)} Negatives from history.")
    
    device = 'cpu' # Force CPU for safety on GTX 1050
    print(f"[Trainer] Device: {device}")
    
    # 2. Initialize Model
    print(f"[Trainer] Loading Backbone: {MODEL_NAME}")
    embedder = SentenceTransformer(MODEL_NAME, device=device)
    
    classifier = nn.Sequential(
        nn.Linear(768, 64),
        nn.ReLU(),
        nn.Linear(64, 1),
        nn.Sigmoid()
    ).to(device)
    
    # Load existing weights if avail
    if os.path.exists(WEIGHTS_PATH):
        classifier.load_state_dict(torch.load(WEIGHTS_PATH, map_location=device))
        print("[Trainer] Loaded existing weights to fine-tune.")
    
    # 3. Prepare Dataset
    dataset = PreferenceDataset(positives, negatives, embedder)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    criterion = nn.BCELoss()
    optimizer = optim.Adam(classifier.parameters(), lr=0.001)
    
    # 4. Training Loop
    classifier.train()
    for epoch in range(EPOCHS):
        total_loss = 0
        for embeddings, labels in loader:
            embeddings = embeddings.to(device)
            labels = labels.float().unsqueeze(1).to(device)
            
            optimizer.zero_grad()
            outputs = classifier(embeddings)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {total_loss:.4f}")
        
    # 5. Save
    torch.save(classifier.state_dict(), WEIGHTS_PATH)
    print(f"[Trainer] Saved new weights to {WEIGHTS_PATH}")
    print(">>> The Gatekeeper will now use these learned preferences for the next run.")

if __name__ == "__main__":
    train_irl_head()
