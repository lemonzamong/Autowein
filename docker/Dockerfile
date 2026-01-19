FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# We list them explicitly to avoid copying requirements.txt initially if we want good caching, 
# but for simplicity we'll just install key libs.
RUN pip install --no-cache-dir \
    transformers \
    datasets \
    peft \
    trl \
    accelerate \
    scipy

# Copy source code and data
COPY . /app

# Set default command
# We use CUDA_VISIBLE_DEVICES inside the container, passed via --gpus or env vars
CMD ["python", "src/training/train_finetune.py"]
