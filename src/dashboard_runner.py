import subprocess
import sys
from pathlib import Path

def run_dashboard(port: int = 8501, browser: bool = True):
    dashboard_path = Path(__file__).parent / "ui" / "dashboard.py"

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.port", str(port)
    ]

    if not browser:
        cmd += ["--server.headless", "true"]
    
    subprocess.run(cmd)