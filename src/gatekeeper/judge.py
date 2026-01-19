from typing import List, Dict, Any
import json
import os
from src.core.models import NewsItem
from src.analyst.llm import OpenAIClient, GeminiClient, MockLLM

class Judge:
    """
    [Stage 1.8] The Judge
    Re-ranks top items using LLM-based Strategic Importance assessment.
    """
    def __init__(self, api_key: str = None, use_gemini: bool = False, model: str = None):
        # Model defaults:
        # OpenAI -> gpt-4o-mini
        # Gemini -> gemini-3-flash-preview
        
        if use_gemini and api_key:
            model = model or "gemini-3-flash-preview"
            self.llm = GeminiClient(api_key=api_key, model=model)
            self.enabled = True
            print(f"[Judge] Enabled with Google Gemini ({model})")
        elif api_key or os.getenv("OPENAI_API_KEY"):
            model = model or "gpt-4o-mini"
            self.llm = OpenAIClient(api_key=api_key, model=model)
            self.enabled = True
            print(f"[Judge] Enabled with OpenAI ({model})")
        else:
            print("[Judge] No API Key found. Judge disabled (fallback to Mock).")
            self.llm = MockLLM()
            self.enabled = False

    def evaluate_batch(self, items: List[NewsItem]) -> List[NewsItem]:
        """
        Evaluate a batch of items (sequential or small batch calls).
        Adds 'llm_score' and 'llm_reason' to scores_breakdown.
        """
        if not items:
            return []
            
        print(f"[Judge] Assessing {len(items)} items with {self.llm.model}...")
        
        # We'll process one by one for better reliability, or small batches if latency matters.
        # For ~50 items, sequential is acceptable (approx 1-2s per item = ~1-2 mins total).
        # We can optimize to batch 5 at a time in future if needed.
        
        ranked_items = []
        for item in items:
            scored_item = self._evaluate_single(item)
            ranked_items.append(scored_item)
            
        # Sort by Final LLM Score (Weighted or Replacement)
        # Strategy: Valid LLM score completely overrides Heuristic Score for the final sort?
        # Or Hybrid? Plan said "Re-ranking", implying LLM authority.
        # We will update 'relevance_score' with the LLM verdict (normalized 0-1).
        
        ranked_items.sort(key=lambda x: x.scores_breakdown.get('llm_score', 0), reverse=True)
        return ranked_items

    def _evaluate_single(self, item: NewsItem) -> NewsItem:
        if not self.enabled:
            # Mock behavior
            item.scores_breakdown['llm_score'] = item.relevance_score
            item.scores_breakdown['llm_reason'] = "Mock Judge (No API Key)"
            return item

        system_prompt = """You are a Strategic Intelligence Analyst for the Automotive & Global Mobility Sector. 
Your job is to evaluate news articles for their "Strategic Importance".

Scoring Criteria (0-10):
- 10 (Critical): Major industry shift, breaking tech breakthrough, pivotal policy change, or massive geopolitical event affecting supply chains.
- 7-9 (High): Significant corporate moves (mergers, big investments), key product launches, or notable regulatory updates.
- 4-6 (Medium): Routine earning reports, minor product updates, local market news.
- 0-3 (Low): Generic PR, fluff pieces, redundant coverage, or Clickbait/Spam that slipped through filters.

Output Format: JSON with keys 'score' (float 0-10) and 'reason' (concise 1-sentence thought)."""

        user_prompt = f"Title: {item.title}\nSource: {item.source}\nContent Snippet: {item.content[:500]}..."
        
        try:
            response = self.llm.complete(user_prompt, system_prompt)
            # Parse JSON from response (handle potential markdown fences)
            clean_resp = response.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_resp)
            
            score_10 = float(data.get('score', 0))
            reason = data.get('reason', 'No reason provided')
            
            # Normalize to 0-1 for system compatibility
            llm_score = min(score_10 / 10.0, 1.0)
            
            item.scores_breakdown['llm_score'] = llm_score
            item.scores_breakdown['llm_reason'] = reason
            
            # Update main relevance score to reflect the Judge's verdict
            item.relevance_score = llm_score
            
        except Exception as e:
            print(f"[Judge] Error evaluating '{item.title[:20]}': {e}")
            item.scores_breakdown['llm_score'] = item.relevance_score # Fallback
            item.scores_breakdown['llm_reason'] = f"Error: {str(e)}"
            
        return item
