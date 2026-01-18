#!/bin/bash
echo '=== Autowein Training Launcher ==='

# 1. Build Docker Image
echo '[1/2] Building Docker Image...'
docker build -t autowein-trainer .

# 2. Run Container on GPUs 1 and 2
echo '[2/2] Running Training on GPUs 1 and 2...'
mkdir -p models
# Using explicit device selection
docker run --rm \
    --gpus '"device=1,2"' \
    -v $(pwd)/models:/app/models \
    autowein-trainer

echo 'Done. Check models/autowein_finetuned for artifacts.'
