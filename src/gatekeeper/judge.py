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
            # model = model or "gemini-3-flash-preview"
            model = model or "gemini-2.0-flash-lite"
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
        Evaluate items in batches to optimize API usage and respect rate limits.
        """
        import time
        
        if not items:
            return []
            
        print(f"[Judge] Assessing {len(items)} items with {self.llm.model}...")
        
        # Determine Batch Size
        # Gemini Flash has huge context, can handle 10-20 easily.
        BATCH_SIZE = 10 
        # Rate Limit: Free tier is ~15 RPM => 1 request every 4 seconds.
        # We add 4s sleep to be safe.
        DELAY_SECONDS = 4
        
        ranked_items = []
        chunks = [items[i:i + BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]
        
        total_chunks = len(chunks)
        print(f"[Judge] Processing {total_chunks} batches (Batch Size: {BATCH_SIZE})...")
        
        for i, chunk in enumerate(chunks):
            try:
                print(f"[Judge] Batch {i+1}/{total_chunks} processing...")
                scored_chunk = self._evaluate_chunk_optimized(chunk)
                ranked_items.extend(scored_chunk)
                
                # Rate Limit Sleep
                if i < total_chunks - 1: # Don't sleep after last batch
                    time.sleep(DELAY_SECONDS)
                    
            except Exception as e:
                print(f"[Judge] Critical Batch Error: {e}")
                ranked_items.extend(chunk) # Return original items on crash

        # Update scores and sort
        ranked_items.sort(key=lambda x: x.scores_breakdown.get('llm_score', 0), reverse=True)
        return ranked_items

    def _evaluate_chunk_optimized(self, chunk: List[NewsItem]) -> List[NewsItem]:
        if not self.enabled:
             for item in chunk:
                 item.scores_breakdown['llm_score'] = item.relevance_score
                 item.scores_breakdown['llm_reason'] = "Mock Judge"
             return chunk

        # Prepare Batch Prompt
        items_text = ""
        for idx, item in enumerate(chunk):
            items_text += f"""
[Item {idx+1}]
ID: {item.id}
Title: {item.title}
Source: {item.source}
Snippet: {item.content[:300]}
"""

        system_prompt = """You are a Strategic Intelligence Analyst. Evaluate the "Strategic Importance" of these news items.

Criteria (0-10):
- 10: Critical breakthrough, massive policy shift, supply chain shock.
- 7-9: Major corporate move, key product launch.
- 4-6: Routine earnings, minor updates.
- 0-3: PR fluff, spam, irrelevant.

Output JSON List of objects:
[
  {"id": "...", "score": 8.5, "reason": "..."}
]
Ensure the ID matches exactly."""

        user_prompt = f"Evaluate these {len(chunk)} items:\n{items_text}"

        # Retry logic for 503 Overloaded errors
        max_retries = 3
        backoff = 2
        response = None
        
        for attempt in range(max_retries):
            try:
                response = self.llm.complete(user_prompt, system_prompt)
                if response:
                    break
            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "Overloaded" in err_str or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt < max_retries - 1:
                        # 429 often asks for ~10s wait. Let's be generous.
                        # Backoff: 10s, 20s, 40s
                        initial_wait = 12
                        sleep_time = initial_wait * (2 ** attempt)
                        
                        print(f"[Judge] API Rate Limit/Overload ({'429' if '429' in err_str else '503'}). Retrying in {sleep_time}s...")
                        import time
                        time.sleep(sleep_time)
                        continue
                print(f"[Judge] Warning: LLM Error on attempt {attempt+1}: {e}")

        if response is None:
            print(f"[Judge] Error: LLM returned None after retries for batch {chunk[0].id}...")
            response = "[]" # Treat as empty response
            
        try:
            clean_resp = response.replace('```json', '').replace('```', '').strip()
                
            # Robust parsing (sometimes model returns just array, sometimes wrapped)
            if '{' in clean_resp and '[' not in clean_resp[:10]: 
                 # Try to find list
                 import re
                 match = re.search(r'\[.*\]', clean_resp, re.DOTALL)
                 if match: clean_resp = match.group(0)
            
            results = json.loads(clean_resp)
            
            # Map results back to items
            result_map = {res['id']: res for res in results if 'id' in res}
            
            for item in chunk:
                if item.id in result_map:
                    res = result_map[item.id]
                    score_10 = float(res.get('score', 0))
                    item.scores_breakdown['llm_score'] = min(score_10 / 10.0, 1.0)
                    item.scores_breakdown['llm_reason'] = res.get('reason', 'Batch Evaluated')
                    item.relevance_score = item.scores_breakdown['llm_score']
                else:
                    # Fallback if model missed an item
                    item.scores_breakdown['llm_score'] = item.relevance_score
                    item.scores_breakdown['llm_reason'] = "Batch Missed"
                    
        except Exception as e:
            print(f"[Judge] Error in batch: {e}")
            # Fallback
            for item in chunk:
                 item.scores_breakdown['llm_score'] = item.relevance_score
                 item.scores_breakdown['llm_reason'] = f"Batch Error: {e}"

        return chunk



    def _evaluate_single(self, item: NewsItem) -> NewsItem:
        # Legacy single method (kept if needed, but unused by new batch logic)
        return item
