# =============================================================================
# 1. IMPORT LIBRARIES
# =============================================================================
import cv2
import argparse
from ultralytics import YOLO
import numpy as np
import cvzone
import json
import os
import serial  # <-- ADDED for serial communication
import time    # <-- ADDED for delay after connection

# =============================================================================
# 2. ROI SELECTION SETUP (No changes in this section)
# =============================================================================

# --- Global variables for mouse callback ---
drawing = False
roi_points = []

def select_roi_callback(event, x, y, flags, param):
    global drawing, roi_points
    frame_copy = param['frame'].copy()
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        roi_points = [(x, y)]
        print(f"ROI selection started at: [{x}, {y}]")
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            cv2.rectangle(frame_copy, roi_points[0], (x, y), (0, 255, 0), 2)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        roi_points.append((x, y))
        cv2.rectangle(frame_copy, roi_points[0], roi_points[1], (0, 255, 0), 2)
        print(f"ROI selection ended at: [{x}, {y}]")
    cv2.imshow("Select ROI", frame_copy)

def select_roi(source):
    global roi_points
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print("Error: Could not open video source for ROI selection.")
        return None
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Error: Could not read the first frame for ROI selection.")
        return None
    window_name = "Select ROI"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, select_roi_callback, {'frame': frame})
    print("\n--- ROI Selection Mode ---")
    print("Click and drag to draw the detection area.")
    print("Press 'c' to confirm your selection.")
    print("Press 'q' to quit without saving.")
    cv2.imshow(window_name, frame)
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            if len(roi_points) == 2:
                x1, y1 = roi_points[0]
                x2, y2 = roi_points[1]
                roi = (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
                with open('roi.json', 'w') as f:
                    json.dump(roi, f)
                print(f"ROI saved to roi.json: {roi}")
                break
            else:
                print("Please draw a rectangle first by clicking and dragging.")
        elif key == ord('q'):
            roi_points = []
            roi = None
            print("ROI selection cancelled.")
            break
    cv2.destroyAllWindows()
    return roi if roi_points else None

# =============================================================================
# 3. DETECTION, COUNTING, AND SERIAL COMMUNICATION IN ZONE
# =============================================================================

def detect_in_zone(source, roi_coords, port=None): # <-- ADDED port argument
    """
    Detects, tracks, counts humans, and sends the count via serial.
    """
    # --- Serial Connection Setup ---
    esp_serial = None
    if port:
        try:
            # Establish connection to the specified COM port
            esp_serial = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)  # Wait for the microcontroller to reset
            print(f"Successfully connected to device on {port}")
        except serial.SerialException as e:
            print(f"Error: Could not connect to port {port}. {e}")
            print("Running detection without serial communication.")
    
    # --- Model and Video Setup ---
    model = YOLO('yolov8n.pt')
    person_class_id = list(model.names.keys())[list(model.names.values()).index('person')]
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: Cannot open video source: {source}")
        return
    rx, ry, rw, rh = roi_coords
    
    # Variable to track the last sent count to avoid flooding the serial port
    last_sent_count = -1

    try:
        # Main loop for processing video frames
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Stream ended or could not read frame.")
                break

            cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (255, 0, 0), 2)
            results = model.track(frame, persist=True, classes=[person_class_id], conf=0.5, verbose=False)
            
            humans_in_zone = 0
            if results[0].boxes.id is not None:
                ids = results[0].boxes.id.cpu().numpy().astype(int)
                boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)

                for track_id, box in zip(ids, boxes):
                    x1, y1, x2, y2 = box
                    person_box_area = (x2 - x1) * (y2 - y1)
                    inter_x1, inter_y1 = max(x1, rx), max(y1, ry)
                    inter_x2, inter_y2 = min(x2, rx + rw), min(y2, ry + rh)
                    inter_width, inter_height = max(0, inter_x2 - inter_x1), max(0, inter_y2 - inter_y1)
                    intersection_area = inter_width * inter_height
                    
                    overlap_ratio = 0
                    if person_box_area > 0:
                        overlap_ratio = intersection_area / person_box_area
                    
                    if overlap_ratio >= 0.5:
                        humans_in_zone += 1
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cvzone.putTextRect(frame, f'Person {track_id}', (x1, y1), scale=1.5, thickness=2, offset=5)
            
            # --- SEND DATA TO MICROCONTROLLER ---
            # Only send if the port is connected and the count has changed
            if esp_serial and humans_in_zone != last_sent_count:
                try:
                    # Format the message with a newline character, e.g., "3\n"
                    message = f"{humans_in_zone}\n"
                    esp_serial.write(message.encode()) # Send the message as bytes
                    print(f"Sent to device: {humans_in_zone}")
                    last_sent_count = humans_in_zone
                except serial.SerialException as e:
                    print(f"Error writing to serial port: {e}")
                    # Stop trying to send data if there's an error
                    esp_serial.close()
                    esp_serial = None

            # --- Display Count and Frame ---
            count_text = f"Humans in Zone: {humans_in_zone}"
            cvzone.putTextRect(frame, count_text, (50, 50), scale=2, thickness=2, offset=10, colorR=(0, 0, 255))
            cv2.imshow("Human Counting in Zone", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        # --- Release Resources ---
        print("Closing resources...")
        cap.release()
        cv2.destroyAllWindows()
        if esp_serial and esp_serial.is_open:
            # Send a final '0' to reset the device state before closing
            esp_serial.write(b'0\n')
            esp_serial.close()
            print("Serial connection closed.")

# =============================================================================
# 4. MAIN EXECUTION BLOCK
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLOv8 Human Counter in a defined Zone")
    parser.add_argument("--source", type=str, required=True, help="Path to video file or '0' for webcam.")
    # --- ADDED ARGUMENT FOR SERIAL PORT ---
    parser.add_argument("--port", type=str, help="Serial port for microcontroller (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux).")
    args = parser.parse_args()

    cap_source = 0 if args.source == '0' else args.source
    roi = None

    if os.path.exists('roi.json'):
        while True:
            choice = input("An ROI is already defined. (U)se it or (D)efine a new one? ").lower()
            if choice == 'u':
                with open('roi.json', 'r') as f:
                    roi = tuple(json.load(f))
                break
            elif choice == 'd':
                roi = select_roi(cap_source)
                break
            else:
                print("Invalid choice. Please enter 'u' or 'd'.")
    else:
        print("No ROI file found. Please define a new area.")
        roi = select_roi(cap_source)

    if roi:
        print(f"Starting detection with ROI: {roi}")
        # --- PASS THE PORT ARGUMENT TO THE FUNCTION ---
        detect_in_zone(cap_source, roi, args.port)
    else:
        print("No ROI was defined. Exiting the program.")