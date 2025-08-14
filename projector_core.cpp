// projector_core.cpp
// A performance-critical C++ module to project 2D points into a 3D voxel grid.
// This is compiled into a Python module using pybind11.

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>

namespace py = pybind11;

// A simple 3D vector struct for clarity.
struct Vec3 {
    double x, y, z;
};

/*
 * Projects a single ray from a virtual camera through a 2D pixel coordinate
 * and marks the voxels it passes through in a 3D grid.
 *
 * This function is the core of the C++ acceleration. It takes all necessary
 * parameters from Python, performs the heavy iterative calculations, and modifies
 * the numpy array (voxel_grid) in place.
 *
 * Args:
 * voxel_grid: A 3D numpy array representing the volumetric space.
 * p_x, p_y: The (x, y) coordinates of the detected object in the 2D image.
 * cam_pos_x, cam_pos_y, cam_pos_z: The 3D position of the virtual camera.
 * img_w, img_h: The width and height of the input video frame.
 * fov_degrees: The horizontal field of view of the virtual camera.
 * grid_size: The dimension of the voxel grid (assumed to be a cube, e.g., 256).
 * grid_world_size: The size of the voxel grid in world units (e.g., 1000.0).
 * brightness: The value to add to each activated voxel.
*/
void project_ray_to_voxels(
    py::array_t<float> voxel_grid_py,
    int p_x, int p_y,
    double cam_pos_x, double cam_pos_y, double cam_pos_z,
    int img_w, int img_h,
    double fov_degrees,
    int grid_size,
    double grid_world_size,
    float brightness)
{
    // Get direct, unchecked access to the numpy array's buffer.
    // This is fast but requires careful handling of indices.
    auto voxel_grid = voxel_grid_py.mutable_unchecked<3>();

    // --- 1. Calculate Ray Direction ---
    // Convert the 2D pixel coordinate into a 3D direction vector in camera space.
    // This simulates projecting from the image plane of a pinhole camera.

    double fov_rad = fov_degrees * (M_PI / 180.0);
    // Focal length is derived from the field of view and image width.
    double focal_length = (static_cast<double>(img_w) / 2.0) / std::tan(fov_rad / 2.0);

    // Convert pixel coordinates to camera space coordinates.
    // The camera is assumed to be looking down its -Z axis.
    Vec3 ray_cam;
    ray_cam.x = static_cast<double>(p_x) - static_cast<double>(img_w) / 2.0;
    ray_cam.y = static_cast<double>(p_y) - static_cast<double>(img_h) / 2.0;
    ray_cam.z = -focal_length; // Pointing "into" the screen

    // Normalise the direction vector to make it a unit vector.
    double norm = std::sqrt(ray_cam.x * ray_cam.x + ray_cam.y * ray_cam.y + ray_cam.z * ray_cam.z);
    if (norm > 1e-6) {
        ray_cam.x /= norm;
        ray_cam.y /= norm;
        ray_cam.z /= norm;
    }

    // For this simplified model, camera space is aligned with world space.
    // In a more complex system, we'd apply the camera's rotation matrix here.
    Vec3 ray_world_dir = ray_cam;
    Vec3 ray_origin = {cam_pos_x, cam_pos_y, cam_pos_z};

    // --- 2. Ray Marching through Voxel Grid (Amanatides-Woo Algorithm style) ---
    // This is a simplified version of a fast voxel traversal algorithm.

    double voxel_size = grid_world_size / static_cast<double>(grid_size);
    double grid_half_size = grid_world_size / 2.0;

    // Calculate the intersection of the ray with the bounding box of the grid.
    // For simplicity, we assume the grid is centered at the origin.
    // TODO: Add proper ray-AABB intersection for grids not centered at origin.
    double t_max = grid_world_size * 2.0; // A safe maximum distance to march.

    int step_count = 500; // Number of steps to take along the ray.
    double step_size = t_max / step_count;

    for (int i = 0; i < step_count; ++i) {
        double t = i * step_size;
        Vec3 current_point = {
            ray_origin.x + t * ray_world_dir.x,
            ray_origin.y + t * ray_world_dir.y,
            ray_origin.z + t * ray_world_dir.z
        };

        // Convert the world point to voxel grid indices.
        // The grid's world coordinates range from [-half_size, +half_size].
        int ix = static_cast<int>(((current_point.x + grid_half_size) / grid_world_size) * grid_size);
        int iy = static_cast<int>(((current_point.y + grid_half_size) / grid_world_size) * grid_size);
        int iz = static_cast<int>(((current_point.z + grid_half_size) / grid_world_size) * grid_size);

        // Check if the calculated indices are within the bounds of the grid.
        if (ix >= 0 && ix < grid_size && iy >= 0 && iy < grid_size && iz >= 0 && iz < grid_size) {
            // If so, "activate" the voxel by adding the brightness value.
            // Using atomic add would be necessary in a multi-threaded context.
            voxel_grid(ix, iy, iz) += brightness;
        }
    }
}

// --- Pybind11 Module Definition ---
// This is the boilerplate that exposes our C++ function to Python.
PYBIND11_MODULE(projector_core, m) {
    m.doc() = "A C++ core module for fast 2D-to-3D voxel projection.";
    m.def("project_ray", &project_ray_to_voxels, "Projects a ray into a 3D numpy voxel grid",
          py::arg("voxel_grid"),
          py::arg("p_x"), py::arg("p_y"),
          py::arg("cam_pos_x"), py::arg("cam_pos_y"), py::arg("cam_pos_z"),
          py::arg("img_w"), py::arg("img_h"),
          py::arg("fov_degrees"),
          py::arg("grid_size"),
          py::arg("grid_world_size"),
          py::arg("brightness")
    );
}
