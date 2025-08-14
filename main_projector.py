# main_projector.py
# This script runs the full 2D-to-3D object tracking and projection pipeline.

import cv2
import numpy as np
import argparse
import time

# Import the C++ core module we compiled with setup.py
try:
    import projector_core
except ImportError:
    print("ERROR: Failed to import 'projector_core'.")
    print("Please make sure you have compiled the C++ module by running:")
    print("python setup.py install")
    exit()

# --- Argument Parsing ---
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", required=True, help="Path to the input video file")
ap.add_argument("-a", "--min-area", type=int, default=50, help="Minimum contour area to be considered an object")
args = vars(ap.parse_args())

def main():
    """
    Main function to run the object detection and 3D projection pipeline.
    """
    # --- Voxel Grid and Camera Setup ---
    GRID_SIZE = 128          # Resolution of the voxel grid (e.g., 128x128x128)
    GRID_WORLD_SIZE = 1000.0 # Size of the grid in virtual "world" units
    
    # Create the 3D numpy array to act as our voxel grid
    voxel_grid = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=np.float32)
    
    # Define the virtual camera's properties
    # Let's place it away from the grid and looking towards the origin
    cam_pos = (0.0, 0.0, -800.0)
    cam_fov = 60.0 # Horizontal field of view in degrees

    # --- Video and 2D Detector Setup ---
    camera = cv2.VideoCapture(args["video"])
    if not camera.isOpened():
        print(f"Error: Could not open video file: {args['video']}")
        return

    # Using MOG2 for background subtraction
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=32, detectShadows=False)

    print("Processing video... Press 'q' to quit.")
    
    frame_count = 0
    start_time = time.time()

    # --- Main Loop ---
    while True:
        grabbed, frame = camera.read()
        if not grabbed:
            break

        # --- Stage 1: 2D Detection ---
        
        # Resize for performance
        h, w, _ = frame.shape
        # Maintain aspect ratio
        scale = 800 / w
        img_w, img_h = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (img_w, img_h))

        # Apply background subtraction to get a foreground mask
        fg_mask = bg_subtractor.apply(frame)

        # Clean up the mask using morphological operations
        # This helps remove noise and consolidate detected regions
        kernel = np.ones((4, 4), np.uint8)
        fg_mask = cv2.threshold(fg_mask, 240, 255, cv2.THRESH_BINARY)[1]
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.dilate(fg_mask, None, iterations=2)

        # Find contours of the objects in the mask
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # --- Stage 2: 3D Projection ---
        
        # Loop over detected contours
        for c in contours:
            # Filter out small, noisy contours
            if cv2.contourArea(c) < args["min_area"]:
                continue

            # Get the centroid (center point) of the contour
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Draw a circle on the 2D frame for visualization
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                cv2.putText(frame, "Object", (cx - 20, cy - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # This is the key step: call our C++ function
                # It will modify the `voxel_grid` numpy array in place.
                projector_core.project_ray(
                    voxel_grid=voxel_grid,
                    p_x=cx, p_y=cy,
                    cam_pos_x=cam_pos[0], cam_pos_y=cam_pos[1], cam_pos_z=cam_pos[2],
                    img_w=img_w, img_h=img_h,
                    fov_degrees=cam_fov,
                    grid_size=GRID_SIZE,
                    grid_world_size=GRID_WORLD_SIZE,
                    brightness=1.0  # Add a value of 1.0 to each hit voxel
                )

        # --- Display and Exit ---
        cv2.imshow("2D Detection", frame)
        # For debugging, we can also show the mask
        # cv2.imshow("Foreground Mask", fg_mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        
        frame_count += 1

    # --- Cleanup and Save ---
    end_time = time.time()
    elapsed = end_time - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    print("\n--- Processing Complete ---")
    print(f"Processed {frame_count} frames in {elapsed:.2f} seconds ({fps:.2f} FPS).")

    # Save the final voxel grid to a file
    output_filename = "voxel_grid.npy"
    np.save(output_filename, voxel_grid)
    print(f"Voxel grid saved to '{output_filename}'.")
    print("Next step: Use a viewer script to visualize this file in 3D.")
    
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

