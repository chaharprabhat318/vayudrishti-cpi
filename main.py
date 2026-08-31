"""
VayuDrishti Universal Root Main
"""
import os
import sys

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app.main import app
except ModuleNotFoundError:
    # If app folder was flattened on upload
    import app.main
    app = app.main.app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    uvicorn.run(app, host=host, port=port)
