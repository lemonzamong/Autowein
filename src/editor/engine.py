from src.core.models import Commentary
from src.analyst.llm import MockLLM
from src.analyst.prompts import CRITIC_SYSTEM_PROMPT

class EditorEngine:
    def __init__(self):
        self.llm = MockLLM()
        
    def review_commentary(self, commentary: Commentary) -> bool:
        """
        Product review logic. Returns True if passed, False otherwise.
        Updates the commentary with a score.
        """
        # In a real system, the Critic Agent would use the LLM to score the content.
        # Here we mock the behavior.
        
        prompt = f"Critique this commentary: {commentary.content}"
        critique = self.llm.complete(prompt, CRITIC_SYSTEM_PROMPT)
        
        # Mock scoring logic
        score = 0.85 # Assume high quality for now
        
        commentary.style_score = score
        commentary.reasoning_trace.append(f"Critic Review: {critique} (Score: {score})")
        
        return score >= 0.8
