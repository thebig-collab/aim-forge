import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Keep user data outside the PyInstaller one-file extraction directory.
# In a packaged Windows build, use the current user's Local AppData folder.
if getattr(sys, "frozen", False):
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    DATA = base / "AimForge" / "data"
else:
    DATA = Path(__file__).resolve().parent.parent / "data"

DATA.mkdir(parents=True, exist_ok=True)
P = DATA / "profiles.json"
B = DATA / "benchmarks.json"
S = DATA / "sessions.json"

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

def profiles():
    return load(P, {})

def benchmarks():
    return load(B, [])

def save_profile(name, value):
    items = profiles()
    items[name] = {**value, "updated_at": datetime.now().isoformat(timespec="seconds")}
    save(P, items)

def add_benchmarks(rows):
    items = benchmarks()
    items.extend(rows)
    save(B, items)

def add_session(row):
    items = load(S, [])
    items.append(row)
    save(S, items[-5000:])

def backup(path):
    save(Path(path), {"profiles": profiles(), "benchmarks": benchmarks(), "sessions": load(S, [])})

def restore(path):
    data = load(Path(path), {})
    save(P, data.get("profiles", {}))
    save(B, data.get("benchmarks", []))
    save(S, data.get("sessions", []))
