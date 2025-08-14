# Tracking-Stealth-Aircraft-using-Voxel-grid
Reconstructs the 3D path of faint objects from standard 2D video. Uses OpenCV for initial detection and a high-performance C++ backend to project motion trails into a volumetric voxel grid for analysis and visualisation.
2D-to-3D Faint Object Tracker
Project Status: Core Functionality Implemented ✅
This project implements a computer vision pipeline to detect, track, and project the motion of faint objects from a 2D video source into a 3D voxel space. It addresses the challenge of identifying low-contrast signals in noisy video from consumer-grade cameras and translates their planar movement into a volumetric representation.

The architecture combines a high-level Python interface for ease of use with a C++ backend for performance-critical ray-casting calculations, linked via pybind11.

Project Pipeline
The system operates in two main stages:

Stage 1: 2D Detection & Tracking (Python/OpenCV)

A real-time background subtraction and contour detection algorithm identifies moving objects in the video feed.

Noise reduction techniques (morphological transformations) are applied to filter out sensor noise.

The centroid of each valid object is calculated for each frame.

Stage 2: 3D Voxel Projection (Python/C++)

For each detected 2D object centroid, a ray is projected from a virtual camera position into a 3D grid.

A high-performance C++ module calculates the path of the ray through the 3D voxel grid using a fast traversal algorithm.

The voxels that the ray passes through are "activated" or have their intensity increased, creating a volumetric trail of the object's movement over time.

Technology Stack
Python 3.8+

C++17

OpenCV-Python for 2D image processing.

NumPy for numerical operations.

Pybind11 for creating Python bindings for C++ code.

Installation & Setup
Clone the repository:

git clone https://github.com/YOUR_USERNAME/FaintObjectTracker.git
cd FaintObjectTracker

Create a virtual environment and install Python packages:

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt

Compile the C++ module:
This project uses a C++ extension for performance. You will need a C++ compiler (e.g., GCC on Linux, Clang on macOS, or MSVC on Windows). The setup.py script will handle the compilation process.

python setup.py install

This will build the projector_core.cpp file and make it available as a Python module.

Usage
Run the main projector script and point it to a video file. The script will process the video, perform the 2D-to-3D projection, and save the resulting 3D voxel grid to a file named voxel_grid.npy.

python main_projector.py --video path/to/your/video.mp4

Press q to exit the video stream.

Roadmap & Future Work
This project has a solid foundation, with clear avenues for future development. This section highlights that the project is actively under progress.

[ ] Build a 3D Viewer: Create a separate Python script (viewer.py) using a library like PyVista or Matplotlib to load voxel_grid.npy and render the 3D trajectory.

[ ] Implement Kalman Filter: Integrate a Kalman filter into main_projector.py to create smoother, more robust object tracks before projecting them into 3D. This will help handle temporary object occlusions.

[ ] Optimise C++ Core: Investigate more advanced ray-voxel intersection algorithms (e.g., a more robust Amanatides-Woo implementation) in projector_core.cpp to improve performance and accuracy.

[ ] Multi-Object Tracking: Extend the system to handle and project multiple distinct objects simultaneously, assigning a unique ID to each volumetric trail.

Acknowledgements
The core methodology for projecting 2D motion into a 3D voxel space was inspired by the work of the Pixeltovoxelprojector repository. This project adapts and builds upon those concepts for the specific application of tracking faint objects from noisy video sources.
