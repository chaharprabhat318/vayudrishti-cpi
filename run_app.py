"""
VayuDrishti Universal Application Launcher
"""
import os
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

for sub in ["app", "backend", "backend/app"]:
    p = os.path.join(root_dir, sub)
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

import uvicorn

try:
    from app.main import app
except Exception:
    from main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    print(f"[VayuDrishti] Server listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
