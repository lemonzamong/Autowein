from src.analyst.agents import PlannerAgent, SimulatorAgent, WriterAgent
from src.analyst.llm import MockLLM, OpenAIClient
from src.core.models import NewsItem, Commentary
from typing import Dict, Any
import os

class AnalystEngine:
    def __init__(self, use_openai: bool = False, api_key: str = None):
        if use_openai or os.getenv("OPENAI_API_KEY"):
            self.llm = OpenAIClient(api_key=api_key)
        else:
            self.llm = MockLLM()
            
        self.planner = PlannerAgent("Planner", "Structural Planning", self.llm)
        self.simulator = SimulatorAgent("Simulator", "Counterfactual Reasoning", self.llm)
        self.writer = WriterAgent("Writer", "Content Generation", self.llm)
        
    def generate_commentary(self, news_item: NewsItem, context_data: Dict[str, Any]) -> Commentary:
        # Context for agents
        agent_context = {
            "news": news_item,
            "history": context_data.get("related_events", [])
        }
        
        # 1. Plan
        plan = self.planner.run(agent_context)
        agent_context["plan"] = plan
        
        # 2. Simulate
        simulation = self.simulator.run(agent_context)
        agent_context["simulation"] = simulation
        
        # 3. Write
        draft = self.writer.run(agent_context)
        
        return Commentary(
            news_id=news_item.id,
            title=f"Analysis: {news_item.title}",
            content=draft,
            reasoning_trace=[
                f"Plan: {plan}",
                f"Simulation: {simulation}"
            ],
            referenced_events=[e.id for e in context_data.get("related_events", [])],
            counterfactuals=[simulation]
        )
