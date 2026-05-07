#!/bin/bash
# Start vLLM API server with Qwen3-32B-AWQ
nohup python3 -m vllm.entrypoints.openai.api_server \
  --host 0.0.0.0 --port 8002 \
  --model /workspace/models/qwen3-32b-awq \
  --max-model-len 16384 \
  --quantization awq \
  --gpu-memory-utilization 0.75 \
  --dtype float16 \
  > /workspace/vllm.log 2>&1 &
