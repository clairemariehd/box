import json
import os
import time
from datetime import datetime
from pynput import keyboard

# File paths
TAG_FILE = "tag_names.json"
LOG_FILE = "rfid_log.txt"

# Load existing tag names
def load_tags():
    if os.path.exists(TAG_FILE):
        with open(TAG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tags(tags):
    with open(TAG_FILE, "w") as f:
        json.dump(tags, f, indent=4)

def log_event(event):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] - {event}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Track active tags
tag_names = load_tags()
active_tags = set()
recent_logs = []
current_scan = ""

def update_display():
    clear_screen()
    print("🔹 RFID Scanner - Live Log 🔹")
    print(f"📌 Items in Detection Area: {[f'{tag_names.get(t, t)} ({t})' for t in active_tags]}")
    print("📄 Recent Logs:")
    for log in recent_logs[-5:]:
        print(log)

def on_key_press(key):
    global current_scan
    try:
        if key == keyboard.Key.enter:
            process_scan(current_scan)
            current_scan = ""
        elif hasattr(key, 'char') and key.char is not None:
            current_scan += key.char
    except AttributeError:
        pass

def process_scan(tag_id):
    global recent_logs
    if tag_id not in tag_names:
        tag_names[tag_id] = input(f"🆕 New tag detected! Enter a name for this tag ({tag_id}): ")
        save_tags(tag_names)
        print(f"✅ Tag '{tag_id}' saved as '{tag_names[tag_id]}'")
    if tag_id in active_tags:
        active_tags.remove(tag_id)
        event = f"Tag Removed: {tag_names[tag_id]} ({tag_id})"
    else:
        active_tags.add(tag_id)
        event = f"Tag Added: {tag_names[tag_id]} ({tag_id})"
    log_event(event)
    recent_logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {event}")
    update_display()

def main():
    update_display()
    print("🔄 Waiting for RFID scans... Press ESC to exit.")
    with keyboard.Listener(on_press=on_key_press) as listener:
        listener.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🔴 Exiting program.")
