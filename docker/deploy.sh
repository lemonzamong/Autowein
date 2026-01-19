#!/bin/bash

echo "=== Autowein Cognitive Digital Twin Deployment ==="

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 could not be found."
    exit 1
fi

# 2. Install Dependencies
echo "[Step 1] Installing python dependencies..."
# Create venv if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# 3. Check Neo4j
echo "[Step 2] Checking Neo4j connection..."
# Simple check logic or just warn
echo "Ensure your Neo4j instance is running at bolt://localhost:7687"

# 4. Check OpenAI Key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY is not set. System will run in Mock Mode."
else
    echo "OPENAI_API_KEY detected. System will run in Production Mode."
fi

# 5. Run Services
echo "[Step 3] Starting Services..."
echo "Starting Backend API at port 8000..."
nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

echo "Starting Dashboard at port 8501..."
nohup streamlit run src/dashboard/app.py &

echo "Deployment Complete!"
echo "Dashboard: http://localhost:8501"
echo "API Docs: http://localhost:8000/docs"
