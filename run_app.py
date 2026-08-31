"""
VayuDrishti Application Launcher (Render & Local Ready)
"""
import uvicorn
import os
import sys

# Ensure backend package is on python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    print("=" * 70)
    print(" VAYUDRISHTI (??????????) - REAL-TIME AIRFARE PRICE INDEX FOR MoSPI")
    print(" Ministry of Statistics and Programme Implementation, Government of India")
    print(" Smart India Hackathon (SIH26056)")
    print("=" * 70)
    print(f" Starting Server on http://{host}:{port} ...")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
