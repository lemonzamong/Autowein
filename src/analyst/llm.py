from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

class LLMInterface(ABC):
    @abstractmethod
    def complete(self, user_prompt: str, system_prompt: str = "") -> str:
        pass

class MockLLM(LLMInterface):
    def complete(self, user_prompt: str, system_prompt: str = "") -> str:
        # Simple heuristic response based on prompt content
        if "Planner" in system_prompt or "Plan" in user_prompt:
            return "THOUGHT: I should retrieve context about the topic.\nPLAN: Retrieve(Topic)"
        elif "Simulator" in system_prompt or "Simulate" in user_prompt:
            return "SCENARIO: If X happens, Y will likely follow."
        elif "Writer" in system_prompt:
            return "TITLE: Analysis of Recent Events\nCONTENT: Based on the data, the market is shifting..."
        elif "Critic" in system_prompt:
            return "REVIEW: The analysis is sound. Grade: S"
        return "Mock Response"

class OpenAIClient(LLMInterface):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        if not HAS_OPENAI:
            raise ImportError("OpenAI library not installed.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
    def complete(self, user_prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content
