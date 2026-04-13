# Simple Hand Tracker using CVZone
import cv2
from cvzone.HandTrackingModule import HandDetector

# Initialize the webcam (0 = default camera)
cap = cv2.VideoCapture(1)

# Create hand detector with max 2 hands
detector = HandDetector(maxHands=2, detectionCon=0.8)

# Main loop to process video frames
while True:
    # Read a frame from webcam
    success, img = cap.read()

    # Detect hands in the frame
    hands, img = detector.findHands(img)

    # Check if any hands are detected
    if hands:
        # Get the first hand
        hand1 = hands[0]

        # Get landmark positions
        lmList = hand1["lmList"]

        # Get bounding box info
        bbox = hand1["bbox"]

        # Get finger up/down status (returns list like [0,1,1,1,1])
        fingers = detector.fingersUp(hand1)

        # Print number of fingers up
        print(f"Fingers up: {fingers.count(1)}")

    # Display the image
    cv2.imshow("Hand Tracker", img)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release camera and close windows
cap.release()
cv2.destroyAllWindows()
