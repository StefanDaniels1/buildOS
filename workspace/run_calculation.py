#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run([sys.executable, '/app/workspace/final_co2_calculation.py'], capture_output=False)
sys.exit(result.returncode)
