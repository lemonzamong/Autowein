from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

class LLMInterface(ABC):
    @abstractmethod
    def complete(self, user_prompt: str, system_prompt: str = "") -> str:
        pass

class MockLLM(LLMInterface):
    def complete(self, user_prompt: str, system_prompt: str = "") -> str:
        # Simple heuristic response based on prompt content
        if "Planner" in system_prompt or "Plan" in user_prompt:
            return "THOUGHT: I should retrieve context about the topic.\nPLAN: Retrieve(Topic)"
        elif "Counterfactual" in system_prompt or "Simulate" in user_prompt:
            return "SCENARIO: If X happens, Y will likely follow."
        elif "Autowein" in system_prompt or "Writer" in system_prompt:
            # [Dynamic Mocking] Check if related reports are being used
            extra_context = ""
            if "Related Reports being merged" in user_prompt or "related reports" in user_prompt:
                 # Extract a bit of text to prove we see it
                 try:
                     reports = user_prompt.split("related reports:")[1].strip()[:50]
                     extra_context = f"\n(Synthesized details from related reports: {reports}...)"
                 except:
                     extra_context = "\n(Synthesized details from multiple sources.)"
                     
            return f"TITLE: Analysis of Recent Events\nCONTENT: Based on the data, the market is shifting...{extra_context}"
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

class GeminiClient(LLMInterface):
    def __init__(self, api_key: str, model: str = "gemini-3-flash-preview"):
        if not HAS_GEMINI:
            raise ImportError("Google GenAI library not installed. Run 'pip install google-genai'.")
        self.client = genai.Client(api_key=api_key)
        self.model = model
        
    def complete(self, user_prompt: str, system_prompt: str = "") -> str:
        # Simple concatenation for System Prompt if Config is complex
        # Or try to use system_instruction if supported easily.
        # Let's use the explicit Concatenation for maximum compatibility with the preview model.
        full_prompt = user_prompt
        if system_prompt:
            full_prompt = f"System Instruction:\n{system_prompt}\n\nUser Task:\n{user_prompt}"
            
        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt
        )
        return response.text
