"""
Hand Gesture Relay Control using cvzone on Raspberry Pi
- 1 finger up: Turn Relay 1 ON
- 2 fingers up: Turn Relay 1 OFF
- 3 fingers up: Turn Relay 2 ON
- 4 fingers up: Turn Relay 2 OFF

Controls relays directly via Raspberry Pi GPIO pins
"""

import cv2
from cvzone.HandTrackingModule import HandDetector
from picamera2 import Picamera2
import time
import RPi.GPIO as GPIO

# ============================================
# GPIO Configuration
# ============================================
RELAY1_PIN = 17  # GPIO 17 for Relay 1
RELAY2_PIN = 27  # GPIO 27 for Relay 2

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RELAY1_PIN, GPIO.OUT, initial=GPIO.HIGH)  # HIGH = OFF (active LOW)
GPIO.setup(RELAY2_PIN, GPIO.OUT, initial=GPIO.HIGH)  # HIGH = OFF (active LOW)

# Initialize camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(
    main={"format": "RGB888", "size": (640, 480)}
))
picam2.start()

# Initialize hand detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Relay states
relay1_state = False
relay2_state = False

# Debounce timer to prevent rapid switching
last_action_time = 0
debounce_delay = 1.0  # 1 second delay between actions


def control_relay(relay_num, state):
    """Control relay via Raspberry Pi GPIO (active LOW)"""
    global relay1_state, relay2_state

    if relay_num == 1:
        relay1_state = state
        GPIO.output(RELAY1_PIN, GPIO.LOW if state else GPIO.HIGH)
    elif relay_num == 2:
        relay2_state = state
        GPIO.output(RELAY2_PIN, GPIO.LOW if state else GPIO.HIGH)

    print(f"Relay {relay_num}: {'ON' if state else 'OFF'}")


def count_fingers(hand):
    """Count the number of fingers up"""
    fingers = detector.fingersUp(hand)
    return sum(fingers)


def main():
    global last_action_time

    print("Hand Gesture Relay Control Started (Raspberry Pi GPIO)")
    print("=" * 50)
    print(f"Relay 1: GPIO {RELAY1_PIN}")
    print(f"Relay 2: GPIO {RELAY2_PIN}")
    print("=" * 50)
    print("Controls:")
    print("  1 finger  -> Relay 1 ON")
    print("  2 fingers -> Relay 1 OFF")
    print("  3 fingers -> Relay 2 ON")
    print("  4 fingers -> Relay 2 OFF")
    print("=" * 50)
    print("Press 'q' to quit")

    while True:
        img = picam2.capture_array()

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

        # Display GPIO info
        cv2.putText(img, "GPIO Direct Control (Raspberry Pi)", (50, 280),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Display instructions
        cv2.putText(img, "1=R1 ON | 2=R1 OFF | 3=R2 ON | 4=R2 OFF", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Show image
        cv2.imshow("Hand Gesture Relay Control", img)

        # Key controls
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cv2.destroyAllWindows()
    GPIO.cleanup()


if __name__ == "__main__":
    main()
