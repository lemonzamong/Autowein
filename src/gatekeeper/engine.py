from typing import List
from src.core.models import NewsItem
from src.core.config import DomainConfig
from src.gatekeeper.scraper import RealScraper
from src.gatekeeper.models import IRLRewardModel

class GatekeeperEngine:
    def __init__(self, config: DomainConfig):
        self.config = config
        self.scraper = RealScraper(sources=config.sources)
        self.irl_model = IRLRewardModel()
        # Share the heavy SBERT encoder to save memory
        self._embedder = self.irl_model.encoder
        
    def fetch_and_select(self) -> List[NewsItem]:
        """
        Fetches live news and filters it.
        """
        raw_news = self.scraper.scrape()
        return self.select_news(raw_news)

    def select_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Filters and scores news items based on domain configuration.
        """
        for item in news_items:
            tfidf_score = self._calculate_tfidf_score(item)
            semantic_score = self._calculate_semantic_score(item)
            user_pref_score = self.irl_model.predict_score(item.title + " " + item.content)
            
            # Hybrid Score (Updated for Deep IRL)
            # TF-IDF (Keywords) + Semantic (Topic Vibe) + IRL (User Pref)
            base_score = (tfidf_score * 0.3) + (semantic_score * 0.4) + (user_pref_score * 0.3)
            
            # Reputation Filter (Multiplicative)
            # Dampen scores from unknown sources (potential spam)
            reputation_score = self._calculate_reputation_score(item)
            final_score = base_score * reputation_score
            
            item.relevance_score = final_score
            item.scores_breakdown = {
                "final": round(final_score, 4),
                "base": round(base_score, 4),
                "tfidf": round(tfidf_score, 4),
                "semantic": round(semantic_score, 4),
                "user_pref": round(user_pref_score, 4),
                "reputation": round(reputation_score, 4)
            }
            item.selected = True # Return all for ranking
            
        # 2. Diversity Filter (Clustering)
        # Sort first so the highest score becomes the cluster representative
        news_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        print(f"[Deep IRLEngine] Applying Diversity Clustering...")
        news_items = self._apply_diversity_filter(news_items, threshold=0.75)
        
        return news_items

    def _apply_diversity_filter(self, items: List[NewsItem], threshold: float = 0.75) -> List[NewsItem]:
        """
        [Stage 3.5] Clustering & Diversity
        Groups similar articles and keeps only the highest-scoring representative.
        Others are attached as `related_items`.
        """
        if not items or not self._embedder:
            return items
            
        from sentence_transformers import util
        import torch
        
        # Prepare texts
        texts = [f"{item.title} {item.content}" for item in items]
        
        # Bulk Encode
        embeddings = self._embedder.encode(texts, convert_to_tensor=True, show_progress_bar=False)
        
        # Hybrid Clustering (Title + Semantic)
        kept_items = []
        merged_indices = set()
        
        cos_scores = util.cos_sim(embeddings, embeddings)
        
        # Levenshtein helper
        def get_levenshtein_ratio(s1, s2):
            if len(s1) == 0 or len(s2) == 0: return 0.0
            import Levenshtein # Assuming installed or basic implementation
            return Levenshtein.ratio(s1, s2)
        
        # If Levenshtein lib missing, basic fallback
        try:
             import Levenshtein
        except ImportError:
             # Fallback simple ratio
             from difflib import SequenceMatcher
             def get_levenshtein_ratio(s1, s2):
                 return SequenceMatcher(None, s1, s2).ratio()

        for i in range(len(items)):
            if i in merged_indices:
                continue
                
            rep_item = items[i]
            kept_items.append(rep_item)
            merged_indices.add(i)
            
            for j in range(i + 1, len(items)):
                if j in merged_indices:
                    continue
                
                # Check 1: Title Similarity (Force Merge)
                # Catches reposts: "Tesla Optimus Delayed" vs "Tesla's Optimus Bot Delayed"
                title_sim = get_levenshtein_ratio(rep_item.title, items[j].title)
                if title_sim > 0.85: # Very similar title
                    rep_item.related_items.append(items[j])
                    merged_indices.add(j)
                    continue

                # Check 2: Semantic Similarity (Topic Merge)
                # Lower threshold to 0.70 to group broad topics
                score = cos_scores[i][j].item()
                if score >= 0.70: 
                    rep_item.related_items.append(items[j])
                    merged_indices.add(j)
                    
        print(f"[Deep IRLEngine] Reduced {len(items)} -> {len(kept_items)} items via Hybrid Clustering.")
        return kept_items
        
    def _calculate_tfidf_score(self, item: NewsItem) -> float:
        """
        [Deep IRL Engine v2] TF-IDF Weighted Overlap
        """
        import json
        import math
        import os
        import re

        MODEL_FILE = "data/irl_tfidf_model.json"
        
        if not hasattr(self, '_tfidf_model'):
            if os.path.exists(MODEL_FILE):
                with open(MODEL_FILE, 'r') as f:
                    self._tfidf_model = json.load(f)
            else:
                self._tfidf_model = None

        if not self._tfidf_model:
            return 0.5 
            
        text = (item.title + " " + item.content).lower()
        tokens = [w for w in re.sub(r'[^\w\s]', '', text).split() if len(w) > 1 and not w.isdigit()]
        
        if not tokens: return 0.0

        idf_scores = self._tfidf_model['idf_scores']
        default_idf = self._tfidf_model['default_idf']
        
        score_sum = 0.0
        for token in tokens:
            idf = idf_scores.get(token, default_idf)
            score_sum += idf
            
        norm_score = score_sum / (len(tokens) ** 0.5) if tokens else 0
        return min(1.0, norm_score / 30.0)

    def _calculate_reputation_score(self, item: NewsItem) -> float:
        """
        [Deep IRL Engine v3.5] Source Reputation Learning
        Manually curated lists until external link graph is built.
        """
        from urllib.parse import urlparse
        
        # Known Low Quality / Spam / irrelevant
        BLOCK_LIST = {
            'simplywall.st', 'marketbeat', 'zacks', 'fool.com', 'investorplace', # Finance spam
            'filmogaz', 'el-balad', 'speedme', 'industrytoday', # Low quality / Scrapers
            'prweb', 'businesswire', 'globenewswire', 'prnewswire', # Press Releases
            'cointelegraph', 'benzinga', 'tipranks' # Crypto/Stock spam
        }
        
        # High Quality Global & Regional Trust
        TRUST_LIST = {
            # Global
            'reuters', 'bloomberg', 'ft.com', 'wsj.com', 'nytimes', 'bbc', 'cnn',
            'techcrunch', 'wired', 'theverge', 'arstechnica', 'cnbc',
            # Automotive
            'autonews', 'motortrend', 'caranddriver', 'electrek', 'insideevs',
            # Korea
            'hankyung', 'mk.co.kr', 'etnews', 'yonhap', 'chosun', 'joins', 'donga',
            'zdnet', 'bloter', 
            # Japan / China
            'nikkei', 'scmp', 'asahi', 'yomiuri', 'caixing'
        }

        try:
            domain = urlparse(item.url).netloc.replace('www.', '')
            
            # Google News RSS URLs are useless ("news.google.com"). 
            # Extract source from Title suffix: "Title - SourceName"
            source_name = domain
            if 'google' in domain and ' - ' in item.title:
                source_name = item.title.rsplit(' - ', 1)[-1].strip().lower()
            
            # Normalize source name for matching
            source_Check = source_name.lower().replace(' ', '')
            
            # Check Blocklist first
            if any(spam in source_Check for spam in BLOCK_LIST):
                print(f"[Reputation] Blocked: {source_name}")
                return 0.1 # Nuked
            
            # Check Trustlist
            if any(trust in source_Check for trust in TRUST_LIST):
                return 1.2 # Boosted
                
            # Neutral / Unknown
            return 0.9 # Slight penalty for unknown
            
        except Exception as e:
            print(f"[Reputation] Error: {e}")
            return 0.7
            
    def _calculate_semantic_score(self, item: NewsItem) -> float:
        """
        [Deep IRL Engine v3] Semantic One-Class SVM
        Measures distance from the "Autowein Choice Boundary".
        """
        import os
        import joblib
        import numpy as np
        
        MODEL_FILE = "data/semantic_model.pkl"
        
        if not hasattr(self, '_semantic_model'):
            self._semantic_model = None
            self._semantic_data = None
            
            if os.path.exists(MODEL_FILE):
                try:
                    data = joblib.load(MODEL_FILE)
                    self._semantic_data = data
                    self._semantic_model = data['svm']
                    
                    # Ensure embedder is loaded (if not already shared from IRL model)
                    if self._embedder is None:
                        from sentence_transformers import SentenceTransformer
                        print(f"[Engine] Loading fallback SBERT: {data['embedder_name']}")
                        self._embedder = SentenceTransformer(data['embedder_name'], device='cpu')
                        
                except Exception as e:
                    print(f"[Engine] Failed to load Semantic Model: {e}")
        
        if not self._semantic_model or not self._embedder:
            return 0.5 # Neutral fallback if training not done/failed
            
        # Embed
        text = item.title + " " + item.content
        if len(text) < 5: return 0.0
        
        vector = self._embedder.encode([text])[0]
        
        # Determine Score
        dist = self._semantic_model.decision_function([vector])[0]
        
        # Safe Sigmoid (prevent overflow)
        # Dist range check: typical SVM dist is -2 to +2.
        # If very large/small, clamp.
        dist = max(-10, min(10, dist))
        
        # Sigmoid: 1 / (1 + exp(-dist))
        # Removed *5 scaling to match natural distribution better
        score = 1 / (1 + np.exp(-dist))
        
        return score

