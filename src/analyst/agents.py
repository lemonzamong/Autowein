from src.analyst.llm import MockLLM, LLMInterface
from typing import Dict, Any
from src.analyst.prompts import PLANNER_SYSTEM_PROMPT, SIMULATOR_SYSTEM_PROMPT, WRITER_SYSTEM_PROMPT

class Agent:
    def __init__(self, name: str, role: str, llm: LLMInterface):
        self.name = name
        self.role = role
        self.llm = llm

    def run(self, context: Dict[str, Any]) -> str:
        pass

class PlannerAgent(Agent):
    def run(self, context: Dict[str, Any]) -> str:
        # Context includes news item and historical events
        prompt = f"Create an outline for a commentary on: {context['news'].title}. Context: {context['history']}"
        return self.llm.complete(prompt, PLANNER_SYSTEM_PROMPT)

class SimulatorAgent(Agent):
    def run(self, context: Dict[str, Any]) -> str:
        prompt = f"Run a counterfactual simulation for: {context['news'].title}. What if this didn't happen?"
        return self.llm.complete(prompt, SIMULATOR_SYSTEM_PROMPT)

class WriterAgent(Agent):
    def run(self, context: Dict[str, Any]) -> str:
        prompt = f"Write a commentary based on this outline: {context['plan']}. Incorporate this simulation: {context['simulation']}."
        return self.llm.complete(prompt, WRITER_SYSTEM_PROMPT)
