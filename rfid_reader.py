import json
import os
import time
import threading
from datetime import datetime

# File paths
TAG_FILE = "tag_names.json"
LOG_FILE = "rfid_log.txt"
TIMER_FILE = "tag_timers.json"  # New file to store timer values

# Load existing tag names
def load_tags():
    if os.path.exists(TAG_FILE):
        with open(TAG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tags(tags):
    with open(TAG_FILE, "w") as f:
        json.dump(tags, f, indent=4)

# Load existing timer settings
def load_timers():
    if os.path.exists(TIMER_FILE):
        with open(TIMER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_timers(timers):
    with open(TIMER_FILE, "w") as f:
        json.dump(timers, f, indent=4)

def log_event(event, tag_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] - {event} ({tag_id})\n"
    
    # Open the log file with utf-8 encoding to handle special characters
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Timer function that runs in a separate thread
def start_timer(tag_id, tag_name, timeout_minutes, active_tags, recent_logs, running_timers):
    timer_id = f"{tag_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    running_timers[tag_id] = timer_id
    
    # Convert minutes to seconds
    timeout_seconds = timeout_minutes * 60
    
    # Sleep until timeout
    time.sleep(timeout_seconds)
    
    # Check if this is the most recent timer for this tag and if tag is still outside
    if running_timers.get(tag_id) == timer_id and tag_id not in active_tags:
        notification = f"⏰ ALERT: '{tag_name}' has been outside detection zone for {timeout_minutes} minutes!"
        log_event(f"Timer Alert: {tag_name}", tag_id)
        
        # Add to recent logs
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        recent_logs.append(f"{timestamp} - {notification}")
        
        # Force screen refresh by adding event to a global notification queue
        # This will be shown on next screen refresh

# Main function
def main():
    tag_names = load_tags()
    tag_timers = load_timers()
    active_tags = set()
    recent_logs = []
    running_timers = {}  # Keep track of running timers by tag_id
    
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
        
        # Only show rename option if there are items in the detection area
        if active_tags:
            print("  [rename] - Rename a tag in the detection area")
            
        print("  [timers] - View/edit timer settings")
        print("  [exit] - Exit program")
        
        # Get user input
        command = input("\nEnter command or tag ID: ").strip().lower()
        
        # Process commands
        if command == "exit":
            break
        elif command == "list":
            print("\n🏷️ Known Tags:")
            for tag_id, name in tag_names.items():
                timeout = tag_timers.get(tag_id, "No timer set")
                print(f"  {name} ({tag_id}) - Timeout: {timeout} min")
            input("\nPress Enter to continue...")
        elif command == "scan":
            tag_id = input("Enter tag ID: ").strip()
            process_tag(tag_id, tag_names, tag_timers, active_tags, recent_logs, running_timers)
        elif command == "rename" and active_tags:
            rename_tag(tag_names, active_tags, recent_logs)
        elif command == "timers":
            manage_timers(tag_names, tag_timers)
        else:
            # Treat input as a tag ID
            tag_id = command
            process_tag(tag_id, tag_names, tag_timers, active_tags, recent_logs, running_timers)

def process_tag(tag_id, tag_names, tag_timers, active_tags, recent_logs, running_timers):
    # Validate the tag ID (assuming RFID tags are alphanumeric and of a certain length, e.g., 10 characters)
    if not tag_id.isalnum() or len(tag_id) < 23 or len(tag_id) > 25:
        print("❌ Invalid RFID tag ID.")
        time.sleep(1)
        return

    # Check if this is a new tag
    if tag_id not in tag_names:
        print(f"🆕 New tag detected! ({tag_id})")
        new_name = input("Enter a name for this tag: ").strip()
        tag_names[tag_id] = new_name
        save_tags(tag_names)
        
        # Ask for timer setting
        while True:
            timer_input = input("Enter time in minutes before notification when outside zone (0 for no timer): ")
            try:
                timer_minutes = int(timer_input)
                if timer_minutes >= 0:
                    if timer_minutes > 0:
                        tag_timers[tag_id] = timer_minutes
                        save_timers(tag_timers)
                        log_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - New tag registered: {new_name} with {timer_minutes}min timer"
                    else:
                        log_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - New tag registered: {new_name} with no timer"
                    break
                else:
                    print("❌ Please enter a positive number or 0.")
            except ValueError:
                print("❌ Please enter a valid number.")
        
        recent_logs.append(log_msg)
        
    # Toggle tag presence
    tag_name = tag_names.get(tag_id)
    if tag_id in active_tags:
        # Tag is being removed from the active zone
        active_tags.remove(tag_id)
        event = f"Removed: {tag_name}"
        
        # Start timer if one is set for this tag
        if tag_id in tag_timers and tag_timers[tag_id] > 0:
            timer_minutes = tag_timers[tag_id]
            # Create and start a timer thread
            timer_thread = threading.Thread(
                target=start_timer,
                args=(tag_id, tag_name, timer_minutes, active_tags, recent_logs, running_timers)
            )
            timer_thread.daemon = True  # Thread will terminate when main program exits
            timer_thread.start()
            
            recent_logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Started {timer_minutes}min timer for: {tag_name}")
    else:
        # Tag is being added to the active zone
        active_tags.add(tag_id)
        event = f"Added: {tag_name}"
        
        # Cancel any running timers for this tag
        if tag_id in running_timers:
            running_timers.pop(tag_id, None)
    
    # Log the event
    log_event(event, tag_id)
    recent_logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {event}")

def rename_tag(tag_names, active_tags, recent_logs):
    if not active_tags:
        print("No tags in detection area to rename.")
        time.sleep(1)
        return
    
    # Display available tags to rename
    print("\n🔄 Rename Tag:")
    detected_tags = list(active_tags)
    
    for i, tag_id in enumerate(detected_tags, 1):
        print(f"  {i}. {tag_names.get(tag_id)} ({tag_id})")
    
    # Get tag selection
    try:
        selection_input = input("\nSelect tag number to rename (0 to cancel): ")
        if selection_input == "0":
            return
        
        selection = int(selection_input)
        
        if 1 <= selection <= len(detected_tags):
            selected_tag = detected_tags[selection-1]
            old_name = tag_names.get(selected_tag)
            
            # Get new name
            new_name = input(f"Enter new name for '{old_name}': ").strip()
            
            # Update tag name
            tag_names[selected_tag] = new_name
            save_tags(tag_names)
            
            # Log the rename
            event = f"Renamed: {old_name} → {new_name}"
            log_event(event, selected_tag)
            recent_logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {event}")
            
            print(f"✅ Successfully renamed '{old_name}' to '{new_name}'")
            time.sleep(1)
        else:
            print("❌ Invalid selection.")
            time.sleep(1)
    except ValueError:
        print("❌ Please enter a valid number.")
        time.sleep(1)
    finally:
        time.sleep(1)

def manage_timers(tag_names, tag_timers):
    while True:
        clear_screen()
        print("⏰ Timer Settings")
        print("\nCurrent Timer Settings:")
        
        # Display all tags and their timers
        tag_list = list(tag_names.items())
        for i, (tag_id, name) in enumerate(tag_list, 1):
            timer_value = tag_timers.get(tag_id, "No timer")
            print(f"  {i}. {name}: {timer_value} minutes")
        
        print("\nOptions:")
        print("  [#] - Edit timer for tag number #")
        print("  [back] - Return to main menu")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == "back":
            break
        
        try:
            tag_index = int(choice) - 1
            if 0 <= tag_index < len(tag_list):
                tag_id, name = tag_list[tag_index]
                
                current_timer = tag_timers.get(tag_id, 0)
                print(f"\nCurrent timer for '{name}': {current_timer} minutes")
                
                new_timer_input = input("Enter new timer in minutes (0 to disable): ")
                try:
                    new_timer = int(new_timer_input)
                    if new_timer >= 0:
                        if new_timer > 0:
                            tag_timers[tag_id] = new_timer
                            print(f"✅ Timer for '{name}' set to {new_timer} minutes")
                        else:
                            # Remove timer if it exists
                            if tag_id in tag_timers:
                                del tag_timers[tag_id]
                            print(f"✅ Timer for '{name}' disabled")
                        
                        save_timers(tag_timers)
                    else:
                        print("❌ Please enter a positive number or 0.")
                except ValueError:
                    print("❌ Please enter a valid number.")
                
                time.sleep(1)
            else:
                print("❌ Invalid selection.")
                time.sleep(1)
        except ValueError:
            print("❌ Please enter a valid number or 'back'.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🔴 Exiting program.")