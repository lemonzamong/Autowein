import os
import logging
from typing import List, Optional
import numpy as np

# Try importing necessary ML libraries
try:
    from sentence_transformers import SentenceTransformer
    import torch.nn as nn
    import torch
    HAS_ML = True
except ImportError:
    HAS_ML = False
    print("[Gatekeeper] Warning: 'sentence-transformers' or 'torch' not found. IRL Model will run in basic mode.")

class IRLRewardModel:
    """
    Inverse Reinforcement Learning (IRL) Reward Model.
    Predicts a 'User Preference Score' (0.0 - 1.0) based on news title/content.
    
    Architecture:
    - Backbone: SBERT (e.g., 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    - Head: Linear Classification Layer (trained on 10 years of historical data)
    """
    
    def __init__(self, model_name: str = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2', weights_path: Optional[str] = "data/irl_weights.pth"):
        # Force CPU if using older GPU (GTX 10xx) with new PyTorch
        # The user has GTX 1050 (CC 6.1) but PyTorch wants 7.0+
        self.device = 'cpu' 
        # self.device = 'cuda' if (HAS_ML and torch.cuda.is_available()) else 'cpu'
        
        self.model_name = model_name
        self.encoder = None
        self.classifier = None
        
        if HAS_ML:
            print(f"[Gatekeeper] Loading IRL Reward Model: {model_name} on {self.device}...")
            try:
                self.encoder = SentenceTransformer(model_name, device=self.device)
                
                # Simple Linear Head for binary/regression score
                # This 'Linear Head' is what needs to be trained on top of SBERT.
                self.classifier = nn.Sequential(
                    nn.Linear(768, 64), # 768 for mpnet-base
                    nn.ReLU(),
                    nn.Linear(64, 1),
                    nn.Sigmoid()
                ).to(self.device)
                
                if weights_path and os.path.exists(weights_path):
                    self.classifier.load_state_dict(torch.load(weights_path, map_location=self.device))
                    print(f"[Gatekeeper] Loaded trained Classification Head from {weights_path}")
                else:
                    print(f"[Gatekeeper] No trained Classification Head found at {weights_path}. Using initialized weights (Simulation Mode).")
                    print("             (Note: The SBERT backbone is loaded correctly, only the custom score predictor is untrained.)")
                    
            except Exception as e:
                print(f"[Gatekeeper] Error initializing SBERT: {e}")
                self.encoder = None

    def predict_score(self, text: str) -> float:
        """
        Returns a score between 0.0 and 1.0 indicating user preference.
        """
        if not HAS_ML or self.encoder is None:
            # Fallback heuristic if ML is missing
            return 0.5

        try:
            with torch.no_grad():
                embedding = self.encoder.encode(text, convert_to_tensor=True)
                score = self.classifier(embedding).item()
                return float(score)
        except Exception as e:
            # logging.error(f"Prediction failed: {e}")
            return 0.5

    def batch_predict(self, texts: List[str]) -> List[float]:
        if not HAS_ML or self.encoder is None:
            return [0.5] * len(texts)
            
        try:
            with torch.no_grad():
                embeddings = self.encoder.encode(texts, convert_to_tensor=True)
                scores = self.classifier(embeddings).squeeze().cpu().tolist()
                
                # Handle single item case (float) vs list
                if isinstance(scores, float):
                    return [scores]
                return scores
        except Exception as e:
            print(f"[Gatekeeper] Batch prediction error: {e}")
            return [0.5] * len(texts)
