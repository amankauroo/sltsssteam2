"""
Sign Language Alphabet Detector using cvzone
Detects American Sign Language (ASL) alphabet gestures
"""

import cv2
from cvzone.HandTrackingModule import HandDetector
from cvzone.ClassificationModule import Classifier
import numpy as np
import math
import os

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Width
cap.set(4, 720)   # Height

# Initialize hand detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Image parameters for classification
offset = 20
imgSize = 300

# Labels for ASL alphabet
labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
          "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
          "U", "V", "W", "X", "Y", "Z"]

# Try to load classifier if model exists
classifier = None
model_path = "Model/keras_model.h5"
labels_path = "Model/labels.txt"

if os.path.exists(model_path) and os.path.exists(labels_path):
    try:
        classifier = Classifier(model_path, labels_path)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Could not load model: {e}")
        print("Running in detection-only mode (no classification)")
else:
    print("Model files not found. Running in detection-only mode.")
    print(f"To enable classification, place your trained model at:")
    print(f"  - {model_path}")
    print(f"  - {labels_path}")
    print("\nYou can train a model using Teachable Machine (https://teachablemachine.withgoogle.com/)")


def preprocess_hand_image(img, hand):
    """
    Preprocess the hand image for classification
    Crops and resizes the hand region to a fixed size
    """
    x, y, w, h = hand['bbox']

    # Create white background
    imgWhite = np.ones((imgSize, imgSize, 3), np.uint8) * 255

    # Crop hand region with offset
    y1 = max(0, y - offset)
    y2 = min(img.shape[0], y + h + offset)
    x1 = max(0, x - offset)
    x2 = min(img.shape[1], x + w + offset)

    imgCrop = img[y1:y2, x1:x2]

    if imgCrop.size == 0:
        return None

    # Calculate aspect ratio and resize
    aspectRatio = h / w

    try:
        if aspectRatio > 1:
            # Height is greater than width
            k = imgSize / h
            wCal = math.ceil(k * w)
            imgResize = cv2.resize(imgCrop, (wCal, imgSize))
            wGap = math.ceil((imgSize - wCal) / 2)
            imgWhite[:, wGap:wCal + wGap] = imgResize
        else:
            # Width is greater than height
            k = imgSize / w
            hCal = math.ceil(k * h)
            imgResize = cv2.resize(imgCrop, (imgSize, hCal))
            hGap = math.ceil((imgSize - hCal) / 2)
            imgWhite[hGap:hCal + hGap, :] = imgResize
    except Exception as e:
        return None

    return imgWhite


def detect_gesture_rule_based(hand):
    """
    Rule-based gesture detection for some common ASL letters
    This works without a trained model for basic detection
    """
    fingers = detector.fingersUp(hand)
    total_fingers = sum(fingers)

    # Basic gesture rules (simplified - not full ASL)
    # fingers = [thumb, index, middle, ring, pinky]

    if fingers == [0, 1, 0, 0, 0]:
        return "D"  # Index finger up
    elif fingers == [0, 1, 1, 0, 0]:
        return "V"  # Peace sign
    elif fingers == [1, 1, 0, 0, 0]:
        return "L"  # L shape
    elif fingers == [1, 1, 1, 1, 1]:
        return "B"  # All fingers up (open hand)
    elif fingers == [0, 0, 0, 0, 0]:
        return "A" or "S"  # Fist (could be A or S)
    elif fingers == [0, 1, 1, 1, 0]:
        return "W"  # Three middle fingers up
    elif fingers == [1, 0, 0, 0, 1]:
        return "Y"  # Thumb and pinky out
    elif fingers == [0, 1, 0, 0, 1]:
        return "I"  # Index and pinky
    elif fingers == [1, 1, 1, 0, 0]:
        return "F" or "9"  # Three fingers
    else:
        return None


def main():
    print("Sign Language Alphabet Detector Started")
    print("=" * 50)
    print("Show ASL hand signs to the camera")
    print("Press 'q' to quit")
    print("Press 's' to save current hand image for training")
    print("=" * 50)

    # Create folder for saving images (for training data collection)
    save_folder = "Data"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    counter = 0
    current_letter = "A"  # Change this when collecting data for different letters

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to capture image")
            break

        # Flip image horizontally for mirror effect
        img = cv2.flip(img, 1)
        imgOutput = img.copy()

        # Find hands
        hands, img = detector.findHands(img, draw=True)

        detected_letter = None
        confidence = 0

        if hands:
            hand = hands[0]

            # Preprocess hand image
            imgWhite = preprocess_hand_image(img, hand)

            if imgWhite is not None:
                # Try classifier first if available
                if classifier is not None:
                    try:
                        prediction, index = classifier.getPrediction(
                            imgWhite, draw=False)
                        detected_letter = labels[index]
                        confidence = max(prediction) * 100
                    except Exception as e:
                        # Fall back to rule-based detection
                        detected_letter = detect_gesture_rule_based(hand)
                        confidence = 0
                else:
                    # Use rule-based detection
                    detected_letter = detect_gesture_rule_based(hand)
                    confidence = 0

                # Display the processed hand image
                cv2.imshow("Hand Image", imgWhite)

                # Draw bounding box and label
                x, y, w, h = hand['bbox']

                if detected_letter:
                    # Draw label background
                    cv2.rectangle(imgOutput, (x - offset, y - offset - 50),
                                  (x + 90, y - offset), (255, 0, 255), cv2.FILLED)

                    # Draw letter
                    cv2.putText(imgOutput, detected_letter, (x, y - offset - 10),
                                cv2.FONT_HERSHEY_COMPLEX, 1.5, (255, 255, 255), 2)

                    # Draw bounding box
                    cv2.rectangle(imgOutput, (x - offset, y - offset),
                                  (x + w + offset, y + h + offset), (255, 0, 255), 4)

        # Display detected letter and confidence
        if detected_letter:
            display_text = f"Letter: {detected_letter}"
            if confidence > 0:
                display_text += f" ({confidence:.1f}%)"
            cv2.putText(imgOutput, display_text, (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        else:
            cv2.putText(imgOutput, "Show a sign...", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 3)

        # Display instructions
        cv2.putText(imgOutput, "Press 'q' to quit | 's' to save image", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Show image
        cv2.imshow("Sign Language Detector", imgOutput)

        # Key controls
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('s'):
            # Save image for training data collection
            if hands and imgWhite is not None:
                letter_folder = os.path.join(save_folder, current_letter)
                if not os.path.exists(letter_folder):
                    os.makedirs(letter_folder)
                counter += 1
                save_path = os.path.join(letter_folder, f"Image_{counter}.jpg")
                cv2.imwrite(save_path, imgWhite)
                print(f"Saved: {save_path}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
