#!/bin/bash
cd /workspace/mimir_net
python3 -c "
import sys
sys.path.append('/workspace/mimir_net')
sys.path.append('/workspace/mimir_net/skills')
from althingi_collector import keyra_med_drive
keyra_med_drive()
"
