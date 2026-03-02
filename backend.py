from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import re
import signal

app = FastAPI()

# Enable CORS so the React frontend (port 5173) can talk to this backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants for file paths
VOCAB_FILE = 'C:/Dev/ChinesePracticeApp/vocabulary.json'
PROGRESS_FILE = 'C:/Dev/ChinesePracticeApp/progress.json'

def load_data():
    """
    Loads the master vocabulary and the user's progress from JSON files.
    If progress doesn't exist, initializes a fresh dictionary.
    """
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        vocab = json.load(f)
    
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    else:
        # Default progress structure
        progress = {"missed": [], "corrections": {}, "stats": {}}
    
    # Ensure stats key exists to avoid KeyError
    if "stats" not in progress: 
        progress["stats"] = {}
    return vocab, progress

def save_progress(progress):
    """Saves the current progress dictionary back to the progress.json file."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

@app.get("/api/vocab")
def get_vocab():
    """Returns the full vocabulary (sorted by frequency) and current user progress."""
    vocab, progress = load_data()
    # Sort characters by their original frequency index (Common words first)
    sorted_chars = sorted(vocab.keys(), key=lambda x: vocab[x].get('frequency_index', 9999))
    return {
        "words": [vocab[c] for c in sorted_chars],
        "progress": progress
    }

class ProgressUpdate(BaseModel):
    """Schema for updating a word's performance stats."""
    char: str
    is_correct: bool
    is_manual_correction: bool = False

@app.post("/api/update")
def update_progress(update: ProgressUpdate):
    """
    Updates a word's Right/Wrong tallies. 
    Triggered after every card flip or manual correction.
    """
    vocab, progress = load_data()
    char = update.char
    
    # Initialize stats for word if missing
    if char not in progress["stats"]:
        progress["stats"][char] = {"right": 0, "wrong": 0}
    
    if update.is_correct:
        progress["stats"][char]["right"] += 1
    else:
        progress["stats"][char]["wrong"] += 1
        # Track persistent missed words (optional)
        if char not in progress["missed"]:
            progress["missed"].append(char)
            
    save_progress(progress)
    return progress

@app.post("/api/quit")
def quit_app():
    """
    Endpoint to gracefully shut down the backend.
    In a local dev environment, this helps clean up the process.
    """
    print("Shutdown requested via UI. Saving progress and exiting...")
    # Trigger a SIGTERM or similar to the current process
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "Shutting down"}

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
