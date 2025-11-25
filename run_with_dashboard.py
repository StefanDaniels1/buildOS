"""
buildOS with Dashboard Integration
Wraps run.py to send events to observability dashboard
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import subprocess

# Import the event sender
from send_dashboard_event import send_event

async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_with_dashboard.py <ifc_file>")
        sys.exit(1)
    
    ifc_file = sys.argv[1]
    session_id = f"buildos-{datetime.now().strftime('%H%M%S')}"
    
    print("\n" + "="*80)
    print("🏗️  buildOS with Dashboard Observability")
    print("="*80)
    print(f"📊 Dashboard: http://localhost:5173")
    print(f"📁 IFC File: {ifc_file}")
    print(f"🔖 Session: {session_id}")
    print("="*80 + "\n")
    
    # Send session start
    send_event("SessionStart", session_id=session_id, payload={"ifc_file": ifc_file})
    
    # Send user prompt
    send_event("UserPromptSubmit", session_id=session_id, 
               payload={"prompt": f"Analyze {ifc_file} for CO2 impact"})
    
    print("🚀 Starting IFC analysis...")
    print("📊 Watch progress at: http://localhost:5173\n")
    
    # Run the actual orchestrator with session ID in environment
    try:
        import os
        env = os.environ.copy()
        env['DASHBOARD_SESSION_ID'] = session_id

        result = subprocess.run(
            ["python", "run.py", ifc_file],
            capture_output=False,
            text=True,
            env=env
        )
        
        # Send completion
        if result.returncode == 0:
            send_event("Stop", session_id=session_id, 
                      payload={"status": "success", "message": "Analysis complete"})
            print("\n✅ Analysis complete! Check the dashboard for full timeline.")
        else:
            send_event("Stop", session_id=session_id, 
                      payload={"status": "error", "message": "Analysis failed"})
            print("\n❌ Analysis failed. Check the dashboard for details.")
            
    except Exception as e:
        send_event("Stop", session_id=session_id, 
                  payload={"status": "error", "message": str(e)})
        print(f"\n❌ Error: {e}")
    
    # Send session end
    send_event("SessionEnd", session_id=session_id)
    
    print(f"\n📊 Review timeline: http://localhost:5173")
    print(f"🔖 Session ID: {session_id}")

if __name__ == "__main__":
    asyncio.run(main())
