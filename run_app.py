"""
VayuDrishti Universal Application Launcher (Render, Linux, Windows, macOS)
"""
import os
import sys

# Auto-detect backend folder location
current_dir = os.path.dirname(os.path.abspath(__file__))
possible_paths = [
    os.path.join(current_dir, "backend"),
    os.path.join(current_dir, "vayudrishti-cpi", "backend"),
    current_dir
]

for p in possible_paths:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    print(f"[VayuDrishti] Server starting on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
