#!/bin/bash
# Download Qwen3-32B-AWQ model from Hugging Face
pip install -U huggingface_hub
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='Qwen/Qwen3-32B-AWQ', local_dir='/workspace/models/qwen3-32b-awq', max_workers=2)
"
