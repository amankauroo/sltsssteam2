"""
Hand Gesture Relay Control using cvzone
- 1 finger up: Turn Relay 1 ON
- 2 fingers up: Turn Relay 1 OFF
- 3 fingers up: Turn Relay 2 ON
- 4 fingers up: Turn Relay 2 OFF

Sends HTTP requests to ESP32 Web Server to control relays
"""

import cv2
from cvzone.HandTrackingModule import HandDetector
import time
import requests
import threading

# ============================================
# ESP32 Configuration - Change IP as needed
# ============================================
ESP32_IP = "10.29.57.6"  # Change this to your ESP32's IP address
ESP32_URL = f"http://{ESP32_IP}"

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Width
cap.set(4, 720)   # Height

# Initialize hand detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Relay states
relay1_state = False
relay2_state = False

# Debounce timer to prevent rapid switching
last_action_time = 0
debounce_delay = 1.0  # 1 second delay between actions

# Connection status
esp32_connected = False


def send_relay_command(relay_num, state):
    """Send HTTP request to ESP32 in a separate thread to avoid blocking"""
    global esp32_connected
    try:
        endpoint = "on" if state else "off"
        url = f"{ESP32_URL}/api/{endpoint}?relay={relay_num}"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            esp32_connected = True
            print(f"ESP32: Relay {relay_num} -> {'ON' if state else 'OFF'}")
        else:
            print(f"ESP32 Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        esp32_connected = False
        print(f"ESP32 Connection Error: {e}")


def get_relay_states():
    """Fetch current relay states from ESP32"""
    global relay1_state, relay2_state, esp32_connected
    try:
        response = requests.get(f"{ESP32_URL}/api/state", timeout=2)
        if response.status_code == 200:
            data = response.json()
            relay1_state = bool(data.get("r1", 0))
            relay2_state = bool(data.get("r2", 0))
            esp32_connected = True
    except requests.exceptions.RequestException:
        esp32_connected = False


def control_relay(relay_num, state):
    """Control relay via ESP32 HTTP API"""
    global relay1_state, relay2_state

    if relay_num == 1:
        relay1_state = state
    elif relay_num == 2:
        relay2_state = state

    # Send command in separate thread to avoid blocking camera
    thread = threading.Thread(
        target=send_relay_command, args=(relay_num, state))
    thread.daemon = True
    thread.start()

    print(f"Relay {relay_num}: {'ON' if state else 'OFF'}")


def count_fingers(hand):
    """Count the number of fingers up"""
    fingers = detector.fingersUp(hand)
    return sum(fingers)


def main():
    global last_action_time

    print("Hand Gesture Relay Control Started")
    print("=" * 50)
    print(f"ESP32 Address: {ESP32_URL}")
    print("=" * 50)
    print("Controls:")
    print("  1 finger  -> Relay 1 ON")
    print("  2 fingers -> Relay 1 OFF")
    print("  3 fingers -> Relay 2 ON")
    print("  4 fingers -> Relay 2 OFF")
    print("=" * 50)
    print("Press 'q' to quit")
    print("Press 'r' to refresh relay states from ESP32")

    # Get initial relay states from ESP32
    print("\nConnecting to ESP32...")
    get_relay_states()
    if esp32_connected:
        print("Connected to ESP32!")
    else:
        print("Could not connect to ESP32. Check IP address and network.")

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to capture image")
            break

        # Flip image horizontally for mirror effect
        img = cv2.flip(img, 1)

        # Find hands
        hands, img = detector.findHands(img, draw=True)

        current_time = time.time()

        if hands:
            hand = hands[0]
            fingers_count = count_fingers(hand)

            # Check debounce
            if current_time - last_action_time > debounce_delay:
                if fingers_count == 1:
                    control_relay(1, True)
                    last_action_time = current_time
                elif fingers_count == 2:
                    control_relay(1, False)
                    last_action_time = current_time
                elif fingers_count == 3:
                    control_relay(2, True)
                    last_action_time = current_time
                elif fingers_count == 4:
                    control_relay(2, False)
                    last_action_time = current_time

            # Display finger count on image
            cv2.putText(img, f"Fingers: {fingers_count}", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 255), 3)

        # Display relay states
        relay1_color = (0, 255, 0) if relay1_state else (0, 0, 255)
        relay2_color = (0, 255, 0) if relay2_state else (0, 0, 255)

        cv2.putText(img, f"Relay 1: {'ON' if relay1_state else 'OFF'}", (50, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, relay1_color, 2)
        cv2.putText(img, f"Relay 2: {'ON' if relay2_state else 'OFF'}", (50, 230),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, relay2_color, 2)

        # Display ESP32 connection status
        status_color = (0, 255, 0) if esp32_connected else (0, 0, 255)
        status_text = f"ESP32: {'Connected' if esp32_connected else 'Disconnected'}"
        cv2.putText(img, status_text, (50, 280),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

        # Display instructions
        cv2.putText(img, "1=R1 ON | 2=R1 OFF | 3=R2 ON | 4=R2 OFF", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Show image
        cv2.imshow("Hand Gesture Relay Control", img)

        # Key controls
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            # Refresh relay states from ESP32
            get_relay_states()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
