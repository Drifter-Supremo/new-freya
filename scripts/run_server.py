"""
run_server.py - Quick script to start the FastAPI server
"""
import subprocess
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_server():
    """Run the FastAPI server."""
    print("Starting Freya backend server...")
    print("Server will be available at http://localhost:8000")
    print("API documentation at http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        # Run uvicorn with reload
        subprocess.run([
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    run_server()