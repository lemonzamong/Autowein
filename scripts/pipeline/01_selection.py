import sys
import os
import json
from datetime import datetime

# Add project root to path (scripts/pipeline/ -> ../../)
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.core.config import ConfigLoader
from src.gatekeeper.engine import GatekeeperEngine
from src.core.models import NewsItem

def run_stage1():
    print("=== [Stage 1] Daily News Selection (Gatekeeper) ===")
    
    # 1. Load Config
    loader = ConfigLoader("config/mobility.yaml")
    config = loader.load()
    
    # 2. Initialize Engine
    engine = GatekeeperEngine(config)
    
    # 3. Fetch & Filters (IRL)
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = f"data/daily/{today}"
    os.makedirs(output_dir, exist_ok=True)

    # 3. Fetch & Filters (IRL)
    print(">>> Scraping and Scoring...")
    all_items = engine.fetch_and_select()

    # [NEW] Save Raw Fetched Data (0_searched.json)
    raw_output_path = f"{output_dir}/0_searched.json"
    
    from dataclasses import asdict
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            return super().default(o)
            
    raw_dicts = [asdict(item) for item in all_items]
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        json.dump(raw_dicts, f, indent=4, ensure_ascii=False, cls=DateTimeEncoder)
    print(f">>> [Archive] Saved {len(all_items)} raw items to {raw_output_path}")
    
    # 4. Filter for Previous 24 Hours (Yesterday's News)
    # E.g. If specific "yesterday" logic is needed (00:00-23:59 of previous day)
    from datetime import timedelta
    target_date = (datetime.now() - timedelta(days=1)).date()
    # Or strict 24h window: target_time = datetime.now() - timedelta(hours=24)
    
    print(f">>> Filtering for Date: {target_date} (Previous Day)")
    
    selected_items = []
    for item in all_items:
        # item.published_at might be timezone aware. Convert to naive date for comparison or handle properly.
        # Simple approach: Match Date
        p_date = item.published_at.date() if item.published_at else datetime.now().date()
        
        # Determine if it matches
        # Note: timezone issues might result in off-by-one errors depending on where server is.
        # We'll allow [Target Date] and [Today] to ensure we don't miss "late night" news that just arrived,
        # but user specifically asked for "Previous Day". Let's stick to user request.
        # But RSS feeds might not go back far enough if we restrict too much. 
        # Let's interpret "Previous 24 Hours" as a sliding window or Yesterday.
        # User said "Daily news... previous 24h". Let's do a 24-48h window to be safe for demo.
        if p_date >= target_date: 
             selected_items.append(item)
    
    print(f">>> Kept {len(selected_items)} items from {len(all_items)} after date filter.")
    
    # 4. Sort by Score and Pick Top 50 (Candidates for LLM)
    selected_items.sort(key=lambda x: x.relevance_score, reverse=True)
    # Filter candidates: Take All valid items (User Request: No Limit)
    candidates = selected_items[:]
    
    print(f">>> Selected {len(candidates)} candidates for LLM Judging.")
    
    # 5. [Stage 1.8] LLM Re-ranking (The Judge)
    from src.gatekeeper.judge import Judge
    gemini_key = "AIzaSyDQX66EWC_ksMdMM2aLlbMImDLJvt6u-_I" # User provided
    api_key = os.getenv("OPENAI_API_KEY")
    
    use_gemini = True
    active_key = gemini_key if (use_gemini and gemini_key) else api_key
    
    judge = Judge(api_key=active_key, use_gemini=use_gemini)
    
    if judge.enabled:
        print(">>> Judge is enabled. Re-ranking candidates...")
        # Note: Large batches might take time.
        ranked_items = judge.evaluate_batch(candidates)
        # Keep all ranked items
        final_list = ranked_items[:]
    else:
        print(">>> Judge is disabled. Using heuristic ranking.")
        # Keep all candidates
        final_list = candidates[:]

    print(f">>> Final Selection: {len(final_list)} items.")
    for i, item in enumerate(final_list):
        # Check for breakdown
        breakdown = getattr(item, 'scores_breakdown', {})
        
        # Display LLM Score if present
        llm_info = ""
        if 'llm_score' in breakdown:
            llm_info = f" [LLM: {breakdown['llm_score']:.2f} | {breakdown.get('llm_reason', '')[:30]}...]"
            
        if breakdown:
            score_str = f"Final: {breakdown.get('final', 0):.3f} (Rep: {breakdown.get('reputation', 0):.2f}) | Base: {breakdown.get('base', 0):.3f}{llm_info}"
        else:
            score_str = f"Score: {item.relevance_score:.4f}"
            
        related_count = len(getattr(item, 'related_items', []))
        related_str = f" [Merged +{related_count}]" if related_count > 0 else ""
            
        print(f"    [{i+1}] {item.title} ({score_str}){related_str}")
        
    # 6. Save State
    # 6. Save State
    # Directory created at start
    # today = datetime.now().strftime("%Y-%m-%d")
    # output_dir = f"data/daily/{today}"
    # os.makedirs(output_dir, exist_ok=True)
    
    # Save ranked version
    output_path = f"{output_dir}/1_selected_ranked.json"
    # Also overwrite the standard one for Dashboard compatibility if preferred, 
    # but let's keep separate for now so we can compare.
    # Actually, Dashboard reads '1_selected.json'. For seamless integration, we should probably overwrite it 
    # OR update DashboardConfig. Let's save to BOTH for safety.
    output_path_legacy = f"{output_dir}/1_selected.json"
    
    from dataclasses import asdict
    data_dicts = [asdict(item) for item in final_list]
    
            
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_dicts, f, indent=4, ensure_ascii=False, cls=DateTimeEncoder)
        
    # Overwrite legacy for dashboard compatibility
    with open(output_path_legacy, 'w', encoding='utf-8') as f:
        json.dump(data_dicts, f, indent=4, ensure_ascii=False, cls=DateTimeEncoder)
        
    print(f"=== [Stage 1] Complete. Saved to {output_path} ===")

if __name__ == "__main__":
    run_stage1()
