import subprocess
import sys

result = subprocess.run([sys.executable, '/app/workspace/gen_report.py'])
sys.exit(result.returncode)
