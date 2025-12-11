import json, os
from threading import Lock

LOG_FILE = "logs.json"
_lock = Lock()

def load_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return []

def save_logs(logs):
    with _lock:
        existing = load_logs()
        seen = set((e.get("employee_code"), e.get("timestamp"), e.get("device_ip")) for e in existing)
        new = []
        for l in logs:
            key = (l.get("employee_code"), l.get("timestamp"), l.get("device_ip"))
            if key not in seen:
                existing.append(l)
                seen.add(key)
                new.append(l)
        with open(LOG_FILE, "w") as f:
            json.dump(existing, f, indent=4)
    return new