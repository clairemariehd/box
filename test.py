import usb.core
import usb.util
import time

# Define the Vendor ID (VID) and Product ID (PID) for the RFID scanner
VID = 0xffff
PID = 0x35

# Find the device by its VID and PID
dev = usb.core.find(idVendor=VID, idProduct=PID)

# If the device is not found, raise an error
if dev is None:
    raise ValueError("Device not found")

# Set the active configuration (this step is often required for communication)
dev.set_configuration()

# Function to read data from the device (continual polling)
def read_data(dev, timeout=1000):
    try:
        # Continuously read data from the device's input endpoint
        data = dev.read(0x81, 64, timeout=timeout)  # Read 64 bytes of data at a time
        return data
    except usb.core.USBError as e:
        if e.errno == 110:  # Timeout error, no data available
            return None  # Return None to indicate no data was found, without an error message
        else:
            # Print USB error other than timeout (if any)
            print(f"USB error: {e}")
            return None

# Store the last RFID data to check if it's the same tag
last_rfid_data = None

# Function to convert raw byte data to a human-readable string
def extract_rfid_data(data):
    # Convert raw byte data to a human-readable ASCII string
    # We will ignore non-printable characters and skip them
    filtered_data = []
    
    for byte in data:
        if byte >= 32 and byte <= 126:  # Only printable ASCII characters
            filtered_data.append(chr(byte))
        else:
            filtered_data.append('.')  # Replace non-printable chars with a dot (for readability)

    # Join the filtered data into a string
    filtered_str = ''.join(filtered_data)

    # If the tag is expected to be exactly 24 characters, ensure this length.
    # If it's too long or short, truncate or pad as necessary.
    rfid_tag = filtered_str[:24]  # Limit to the first 24 characters
    return rfid_tag

# Main loop to continually poll for data
try:
    complete_data = []  # Initialize a list to store the received data chunks

    while True:
        data = read_data(dev)  # Poll for data from the RFID scanner

        if data:
            # Add the received data chunk to the complete_data list
            complete_data.extend(data)

            # Debug: Print the raw byte data received (joined all arrays together)
            print("Raw data received:", data)

            # Debug: Print the complete data in ASCII format
            ascii_data = ''.join([chr(byte) if 32 <= byte <= 126 else '.' for byte in complete_data])
            print("Complete data in ASCII:", ascii_data)

            try:
                # Extract the RFID tag from the accumulated data
                rfid_data = extract_rfid_data(complete_data)

                # Print the extracted RFID data
                print(f"Extracted RFID data: {rfid_data}")

                if rfid_data:
                    # Print the RFID data that was detected only once for each scan
                    if rfid_data != last_rfid_data:
                        print(f"New RFID scanned: {rfid_data}")
                        last_rfid_data = rfid_data  # Update the last RFID data
                    else:
                        print("Duplicate RFID, ignoring.")  # If it's the same tag, do nothing.

            except Exception as e:
                print("Error processing data:", e)

            # Clear the complete_data after extracting a full tag (optional)
            complete_data.clear()

        # Sleep for a short period to prevent excessive CPU usage
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Program interrupted")

finally:
    # Clean up and release the device
    usb.util.release_interface(dev, 0)
    usb.util.dispose_resources(dev)
