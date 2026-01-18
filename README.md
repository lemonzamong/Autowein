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

### Deployment & Training (Production)

Since the local machine lacks a powerful GPU, use the pre-packaged archive to deploy to your server (RTX 3090).

**1. Transfer to Server**
The project is already packed into `autowein_production.tar.gz`. Copy it to your GPU server:
```bash
scp autowein_production.tar.gz [USER]@[SERVER_IP]:~/
```

**2. Run Training on Server**
SSH into the server and execute the training script:
```bash
ssh [USER]@[SERVER_IP]
# On the server:
tar -xzf autowein_production.tar.gz
chmod +x run_training_on_server.sh
./run_training_on_server.sh
```
This will:
- Build the `autowein-trainer` Docker image.
- Run `src/training/train_finetune.py` on GPUs 1 & 2.
- Generate the final model adapter in `models/autowein_finetuned`.

## Directory Structure
```
src/
├── core/           # Data models & Config
├── gatekeeper/     # Real News Scraper (BeautifulSoup)
├── historian/      # Neo4j Graph Manager
├── analyst/        # Agents (Planner, Simulator, Writer)
├── editor/         # Critic Engine
├── crawler/        # [NEW] Native 10-Year History Crawler
├── training/       # [NEW] Fine-tuning Pipeline
├── api/            # FastAPI App
└── dashboard/      # Streamlit Demo
```
