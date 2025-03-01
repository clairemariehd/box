import json
import os
import time
from datetime import datetime

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

def log_event(event, tag_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] - {event} ({tag_id})\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Main function
def main():
    tag_names = load_tags()
    active_tags = set()
    recent_logs = []
    
    while True:
        # Clear screen and show current status
        clear_screen()
        print("🔹 RFID Scanner - Live Log 🔹")
        
        # Show items in detection area
        if active_tags:
            item_list = [tag_names.get(t, t) for t in active_tags]
            print(f"📌 Items in Detection Area: {item_list}")
        else:
            print("📌 Items in Detection Area: []")
        
        # Show recent logs
        print("📄 Recent Logs:")
        for log in recent_logs[-5:]:
            print(log)
        
        # Show options
        print("\n📚 Commands:")
        print("  [scan] - Scan an RFID tag")
        print("  [list] - List all known tags")
        print("  [exit] - Exit program")
        
        # Get user input
        command = input("\nEnter command or tag ID: ").strip().lower()
        
        # Process commands
        if command == "exit":
            break
        elif command == "list":
            print("\n🏷️ Known Tags:")
            for tag_id, name in tag_names.items():
                print(f"  {name} ({tag_id})")
            input("\nPress Enter to continue...")
        elif command == "scan":
            tag_id = input("Enter tag ID: ").strip()
            process_tag(tag_id, tag_names, active_tags, recent_logs)
        else:
            # Treat input as a tag ID
            tag_id = command
            process_tag(tag_id, tag_names, active_tags, recent_logs)

def process_tag(tag_id, tag_names, active_tags, recent_logs):
    # Check if this is a new tag
    if tag_id not in tag_names:
        print(f"🆕 New tag detected! ({tag_id})")
        new_name = input("Enter a name for this tag: ").strip()
        tag_names[tag_id] = new_name
        save_tags(tag_names)
        log_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - New tag registered: {new_name}"
        recent_logs.append(log_msg)
        
    # Toggle tag presence
    tag_name = tag_names.get(tag_id)
    if tag_id in active_tags:
        active_tags.remove(tag_id)
        event = f"Removed: {tag_name}"
    else:
        active_tags.add(tag_id)
        event = f"Added: {tag_name}"
    
    # Log the event
    log_event(event, tag_id)
    recent_logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {event}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🔴 Exiting program.")