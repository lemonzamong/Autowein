#!/usr/bin/env python3
import os
import sys
import subprocess

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

def run_stage2():
    print("=== [Stage 2] Human Curation (Streamlit Dashboard) ===")
    print(">>> Launching Streamlit App...")
    
    # Path to app.py
    app_path = os.path.join(os.path.dirname(__file__), "../../src/dashboard/app.py")
    app_path = os.path.normpath(app_path)
    
    if not os.path.exists(app_path):
        print(f"Error: Dashboard app not found at {app_path}")
        return

    # Run Streamlit
    # We use 'sys.executable' -m streamlit to ensure we use the same python env
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n>>> Dashboard closed by user.")
    except Exception as e:
        print(f"Error running dashboard: {e}")

if __name__ == "__main__":
    run_stage2()
