from src.analyst.llm import MockLLM, LLMInterface
from typing import Dict, Any
from src.analyst.prompts import (
    PLANNER_SYSTEM_PROMPT, 
    SIMULATOR_SYSTEM_PROMPT, 
    WRITER_SYSTEM_PROMPT,
    DEVILS_ADVOCATE_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT
)

class Agent:
    def __init__(self, name: str, role: str, llm: LLMInterface):
        self.name = name
        self.role = role
        self.llm = llm

    def run(self, context: Dict[str, Any]) -> str:
        pass

class PlannerAgent(Agent):
    def run(self, context: Dict[str, Any]) -> str:
        # Context includes news item, historical events, AND related news
        related_str = "\n".join(context.get('related_news', []))
        prompt = f"Create an outline for a commentary on: {context['news'].title}.\nContext: {context['history']}\nRelated Reports being merged: {related_str}"
        return self.llm.complete(prompt, PLANNER_SYSTEM_PROMPT)

class SimulatorAgent(Agent):
    def run(self, context: Dict[str, Any]) -> str:
        prompt = f"Run a counterfactual simulation for: {context['news'].title}. What if this didn't happen?"
        return self.llm.complete(prompt, SIMULATOR_SYSTEM_PROMPT)

class DevilsAdvocateAgent(Agent):
    def run(self, context: Dict[str, Any]) -> str:
        prompt = f"""
        Critique this Plan: {context['plan']}
        And this Counterfactual: {context['simulation']}
        
        Identify 3 flaws or missed risks.
        """
        return self.llm.complete(prompt, DEVILS_ADVOCATE_SYSTEM_PROMPT)

class SynthesizerAgent(Agent):
    def run(self, context: Dict[str, Any]) -> str:
        prompt = f"""
        Original Plan: {context['plan']}
        Critique: {context['critique']}
        
        Synthesize a Revised Plan that addresses the critique.
        """
        return self.llm.complete(prompt, SYNTHESIZER_SYSTEM_PROMPT)

class WriterAgent(Agent):
    def run(self, context: Dict[str, Any]) -> str:
        related_str = "\n".join(context.get('related_news', []))
        prompt = f"Write a commentary based on this outline: {context['plan']}.\nIncorporate this simulation: {context['simulation']}.\nAlso synthesize insights from these related reports: {related_str}"
        return self.llm.complete(prompt, WRITER_SYSTEM_PROMPT)
