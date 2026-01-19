from src.analyst.llm import MockLLM, OpenAIClient, GeminiClient
from src.analyst.agents import PlannerAgent, SimulatorAgent, WriterAgent, DevilsAdvocateAgent, SynthesizerAgent
from src.core.models import NewsItem, Commentary
from typing import Dict, Any
import os

class AnalystEngine:
    def __init__(self, use_openai: bool = False, use_gemini: bool = False, api_key: str = None):
        self.llm = MockLLM()
        
        if use_gemini and api_key:
            self.llm = GeminiClient(api_key=api_key)
            print("    > [Analyst] Using Google Gemini Model.")
        elif (use_openai or os.getenv("OPENAI_API_KEY")) and not use_gemini:
            # Fallback to OpenAI if not explicitly using Gemini
            self.llm = OpenAIClient(api_key=api_key)
            print("    > [Analyst] Using OpenAI Model.")
            
        self.planner = PlannerAgent("Planner", "Structural Planning", self.llm)
        self.simulator = SimulatorAgent("Simulator", "Counterfactual Reasoning", self.llm)
        self.devil = DevilsAdvocateAgent("Devil", "Risk Analysis", self.llm)
        self.synthesizer = SynthesizerAgent("Synthesizer", "Logic Synthesis", self.llm)
        self.writer = WriterAgent("Writer", "Content Generation", self.llm)
        
    def generate_commentary(self, news_item: NewsItem, context_data: Dict[str, Any]) -> Commentary:
        # Context for agents
        agent_context = {
            "news": news_item,
            "history": context_data.get("related_events", []),
            "related_news": context_data.get("related_news", [])
        }
        
        # 1. Plan
        plan = self.planner.run(agent_context)
        agent_context["plan"] = plan
        
        # 2. Simulate
        simulation = self.simulator.run(agent_context)
        agent_context["simulation"] = simulation
        
        # 3. Debate Loop (New)
        critique = self.devil.run(agent_context)
        agent_context["critique"] = critique
        
        revised_plan = self.synthesizer.run(agent_context)
        agent_context["plan"] = revised_plan # Update plan for Writer
        
        # 4. Write
        draft = self.writer.run(agent_context)
        
        # Parse Metrics (Confidence & Horizon)
        import re
        confidence = 0.5
        horizon = "Unknown"
        
        # Regex to find "Confidence: 0.X"
        conf_match = re.search(r"Confidence:\s*([0-9.]+)", draft)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
            except: pass
            
        # Regex to find "Horizon: ..."
        hor_match = re.search(r"Horizon:\s*(.+)", draft)
        if hor_match:
            horizon = hor_match.group(1).strip()
            
        # Optional: Clean the metrics block from the text content?
        # User might want to see it, but we store it in metadata.
        # Let's clean it for a polished report.
        if "Metrics:" in draft:
            clean_draft = draft.rsplit("Metrics:", 1)[0].strip()
        else:
            clean_draft = draft
        
        return Commentary(
            news_id=news_item.id,
            title=f"Analysis: {news_item.title}",
            content=clean_draft,
            confidence_score=confidence,
            time_horizon=horizon,
            reasoning_trace=[
                f"Initial Plan: {plan}",
                f"Simulation: {simulation}",
                f"Critique: {critique}",
                f"Revised Plan: {revised_plan}"
            ],
            referenced_events=[e.id for e in context_data.get("related_events", [])],
            counterfactuals=[simulation]
        )
