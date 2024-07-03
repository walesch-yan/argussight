import cv2
import threading
from collections import deque
import time

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from video_processes.flow_detection import FlowDetection

def main():
    # Path to the video file
    video_path = './test_video2.avi'

    # Define the coordinates of the ROI (rectangle)
    roi_x, roi_y, roi_width, roi_height = 500, 500, 300, 450

    # Function to extract frames from a video and save them in a deque
    def extract_frames_to_deque(video_path, frame_deque):
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        frame_count = 0

        # Read and process each frame
        while True:
            ret, frame = cap.read()
            if not ret:
                break  # Break the loop if no frame read

            # Add frame to the deque
            frame_deque.append(frame)

            frame_count += 1

        # Release video capture
        cap.release()

        print(f"Extracted {frame_count} frames.")

    output_deque = deque()

    extract_thread = threading.Thread(target=extract_frames_to_deque, args=(video_path, output_deque))
    extract_thread.start()

    extract_thread.join()

    detector = FlowDetection((roi_x, roi_y, roi_width, roi_height))
    
    '''
    while len(output_deque)>=1:
        frame = output_deque.popleft()
        processed_frame = detector.detect_and_track_features(frame)
        cv2.imshow('Live Stream', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.04)
    '''
    detector.run(output_deque)

if __name__ == "__main__":
    main()