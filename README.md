# Autowein's Cognitive Digital Twin (ACDT)

ACDT is a **Domain-Specific Market Insight Automation System** that mimics the reasoning process of an expert analyst. It leverages **GraphRAG**, **Multi-Agent Systems**, and **Fine-tuned LLMs** to generate high-quality market commentaries.

## Features

- **The Gatekeeper**: Intelligent news crawling and filtering based on Domain Config.
- **The Historian**: A 10-year Knowledge Graph (Neo4j) that provides deep context.
- **The Analyst**: A Multi-Agent Engine (Planner, Simulator, Writer) that drafts insights.
- **The Editor**: A self-reflecting Critic Agent that ensures quality.
- **Dynamic Ontology**: Switch domains (e.g., from Mobility to Bio) just by changing `config.yaml`.

## Quick Start

### Prerequisites
- Python 3.9+
- Neo4j Database (Local or AuraDB)
- OpenAI API Key

### Installation

1. Clone the repository and install dependencies:
```bash
./deploy.sh
```
(This script sets up the venv and installs requirements)

2. Configuration:
   - Edit `config_mobility.yaml` to define your keywords and sources.
   - Set environment variables:
     ```bash
     export OPENAI_API_KEY="sk-..."
     export NEO4J_URI="bolt://localhost:7687"
     export NEO4J_PASSWORD="password"
     ```

### Running the System

**1. Start the API & Dashboard:**
```bash
./deploy.sh
```
This will launch:
- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8501

**2. Fine-tuning (Optional):**
To train the model on your 10-year corpus:
```bash
python3 src/training/train_finetune.py
```

## Directory Structure
```
src/
├── core/           # Data models & Config loader
├── gatekeeper/     # Scraper & IRL Engine
├── historian/      # Neo4j Graph Manager
├── analyst/        # Agents (Planner, Simulator, Writer)
├── editor/         # Critic Engine
├── api/            # FastAPI Application
├── dashboard/      # Streamlit UI
└── training/       # Fine-tuning scripts
```
