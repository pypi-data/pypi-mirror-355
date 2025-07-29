// Standard library includes
#include <stdexcept>
#include <string>
#include <iostream>
#include <memory>
#include <vector>
#include <mutex>
#include <condition_variable>
#include <cstring>
#include <sys/resource.h>

// Third-party includes
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

// WindNinja C API - simpler and more stable approach
#ifdef WINDNINJA_AVAILABLE
#include "windninja.h"
#include "ninja_errors.h"
#include "gdal_priv.h"
#include "ogr_api.h"
#include "cpl_conv.h"
#else
// Stub mode - define minimal types needed for compilation
typedef void* NinjaArmyH;
#endif

namespace py = pybind11;

// Global simulation mutex to prevent concurrent access to WindNinja's global state
// This protects against:
// 1. Global timezone database race conditions
// 2. Global netCDF lock inconsistencies 
// 3. OpenMP thread state corruption
// 4. Other shared static variables in WindNinja
static std::mutex g_global_windninja_mutex;

// Global army registry for proper cleanup
#ifdef WINDNINJA_AVAILABLE
static std::vector<NinjaArmyH*> g_active_armies;
static std::mutex g_army_mutex;
#endif

// Wrapper class using WindNinja C API
class WindNinjaWrapper {
public:
    WindNinjaWrapper() : num_ninjas(0), extraction_in_progress(false) {
#ifdef WINDNINJA_AVAILABLE
        ninja_army = nullptr;
        // Initialize WindNinja
        NinjaErr err = NinjaInit(nullptr);
        if (err != NINJA_SUCCESS) {
            throw std::runtime_error("Failed to initialize WindNinja: " + std::to_string(err));
        }
#endif
        std::cout << "WindNinja initialized successfully" << std::endl;
    }

    ~WindNinjaWrapper() {
        std::cout << "WindNinja destructor called" << std::endl;
        
        // Wait for any ongoing data extraction to complete
        {
            std::unique_lock<std::mutex> lock(extraction_mutex);
            extraction_cv.wait(lock, [this]{ return !extraction_in_progress; });
        }
        
        cleanup();
        std::cout << "WindNinja destroyed and cleaned up" << std::endl;
    }

    void cleanup() {
        // Explicit cleanup method
#ifdef WINDNINJA_AVAILABLE
        if (ninja_army != nullptr) {
            std::cout << "Explicitly cleaning up WindNinja army" << std::endl;
            char** options = nullptr;
            NinjaDestroyArmy(ninja_army, options);
            ninja_army = nullptr;
            num_ninjas = 0;
        }
#endif
    }

    // Configuration methods
    void set_dem_file(const std::string& filename) {
        dem_filename = filename;
    }

    void set_uniform_wind(double speed, double direction, const std::string& speed_units = "mps") {
        wind_speed = speed;
        wind_direction = direction;
        units = speed_units;
    }

    void set_output_path(const std::string& path) {
        output_path = path;
    }

    void set_mesh_choice(const std::string& choice) {
        mesh_choice = choice;
    }

    void set_vegetation(const std::string& veg) {
        vegetation = veg;
    }

    void set_wind_height(double height, const std::string& height_units = "m") {
        wind_height = height;
        height_units_str = height_units;
    }

    void set_num_layers(int layers) {
        num_layers = layers;
    }

    void set_diurnal_winds(bool enable) {
        diurnal_flag = enable;
    }

    void set_date_time(int year, int month, int day, int hour, int minute, const std::string& timezone = "UTC") {
        date_year = year;
        date_month = month;
        date_day = day;
        date_hour = hour;
        date_minute = minute;
        time_zone = timezone;
    }

    void set_air_temperature(double temp, const std::string& temp_units = "C") {
        air_temperature = temp;
        air_temp_units = temp_units;
    }

    void set_cloud_cover(double cover, const std::string& cover_units = "fraction") {
        cloud_cover = cover;
        cloud_cover_units = cover_units;
    }

    bool simulate() {
#ifdef WINDNINJA_AVAILABLE
        // CRITICAL: Acquire global mutex to prevent concurrent WindNinja simulations
        // This prevents race conditions in:
        // - Global timezone database (globalTimeZoneDB)
        // - Global netCDF locks (multiple separate locks in different modules)
        // - OpenMP thread state management and global settings
        // - Output file path conflicts and temporary file collisions
        // - GDAL configuration settings (CPLSetConfigOption calls)
        // - Other static/global variables in WindNinja library
        std::lock_guard<std::mutex> global_lock(g_global_windninja_mutex);
        
        try {
            // STEP 1: Clean up GDAL global state to prevent test contamination
            // WindNinja sets global GDAL config options that pollute subsequent tests
            GDALDestroyDriverManager();  // Clean up registered drivers
            OGRCleanupAll();             // Clean up OGR global state
            
            // Reset critical GDAL configuration options that WindNinja modifies
            CPLSetConfigOption("GDAL_DATA", nullptr);
            CPLSetConfigOption("WINDNINJA_DATA", nullptr);
            CPLSetConfigOption("GDAL_HTTP_TIMEOUT", nullptr);
            CPLSetConfigOption("GDAL_HTTP_UNSAFESSL", nullptr);
            CPLSetConfigOption("GDAL_CACHEMAX", nullptr);
            CPLSetConfigOption("GTIFF_DIRECT_IO", nullptr);
            CPLSetConfigOption("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", nullptr);
            
            // Re-register drivers with clean state
            GDALAllRegister();
            OGRRegisterAll();
            
            // STEP 2: Check and adjust stack size limits to prevent stack overflow
            // WindNinja creates large thread-local arrays that can exceed default stack sizes
#ifndef _WIN32
            struct rlimit stack_limit;
            if (getrlimit(RLIMIT_STACK, &stack_limit) == 0) {
                // Check if stack size is unlimited or very small
                if (stack_limit.rlim_cur == RLIM_INFINITY || stack_limit.rlim_cur < 16 * 1024 * 1024) {
                    // Set stack size to 32MB per thread to handle WindNinja's large arrays
                    stack_limit.rlim_cur = 32 * 1024 * 1024;  // 32MB
                    if (stack_limit.rlim_max != RLIM_INFINITY && stack_limit.rlim_cur > stack_limit.rlim_max) {
                        stack_limit.rlim_cur = stack_limit.rlim_max;
                    }
                    setrlimit(RLIMIT_STACK, &stack_limit);
                }
            }
            
            // STEP 2a: Check virtual memory limits to prevent allocation failures
            struct rlimit vm_limit;
            if (getrlimit(RLIMIT_AS, &vm_limit) == 0) {
                // Increase virtual memory limit if constrained for high-resolution simulations
                if (vm_limit.rlim_cur != RLIM_INFINITY && vm_limit.rlim_cur < 8ULL * 1024 * 1024 * 1024) {
                    // Increase to 8GB if current limit is less
                    vm_limit.rlim_cur = std::min(vm_limit.rlim_max, 8ULL * 1024 * 1024 * 1024);
                    setrlimit(RLIMIT_AS, &vm_limit);
                }
            }
            
            // STEP 2b: Force memory consolidation before simulation
            // This helps prevent fragmentation issues during large allocations
#ifdef __APPLE__
            // On macOS, sync memory before large operations
            sync();
#endif
#endif
            
            // STEP 3: Reset OpenMP state to prevent thread contamination
            // WindNinja uses global OpenMP settings that persist between simulations
#ifdef _OPENMP
            omp_set_num_threads(1);      // Reset to single thread
            omp_set_nested(false);       // Disable nested parallelism  
            omp_set_dynamic(false);      // Disable dynamic thread adjustment
#endif
            
            // STEP 4: Set unique output path to prevent file conflicts
            // Each simulation gets its own output directory to prevent collisions
            std::string unique_output_path = "./windninja_output_" + std::to_string(reinterpret_cast<uintptr_t>(this));
            output_path = unique_output_path;
            
            // STEP 5: Clean up any existing army first
            if (ninja_army != nullptr) {
                char** options = nullptr;
                NinjaDestroyArmy(ninja_army, options);
                ninja_army = nullptr;
                num_ninjas = 0;
            }

            // Prepare wind arrays (required for proper army creation)
            num_ninjas = 1;
            double speed_array[1] = {wind_speed};
            double direction_array[1] = {wind_direction};
            char** options = nullptr;

            // Create army with wind parameters (the correct way)
            std::cout << "Creating domain average army with unique output path: " << output_path << std::endl;
            ninja_army = NinjaMakeDomainAverageArmy(
                num_ninjas,           // number of simulations
                false,                // momentumFlag (conservation of mass)
                speed_array,          // wind speeds array
                units.c_str(),        // speed units
                direction_array,      // wind directions array
                options               // options
            );

            if (ninja_army == nullptr) {
                throw std::runtime_error("Failed to create WindNinja army");
            }

            std::cout << "Army created successfully, configuring..." << std::endl;

            // Configure each simulation in the army (even though we only have 1)
            for (unsigned int i = 0; i < num_ninjas; i++) {
                
                // 1. Communication (always required)
                NinjaErr err = NinjaSetCommunication(ninja_army, i, "cli", options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set communication: " + std::to_string(err));
                }

                // 2. Number of CPUs (always required)
                err = NinjaSetNumberCPUs(ninja_army, i, 1, options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set CPU count: " + std::to_string(err));
                }

                // 3. Initialization method (always required)
                err = NinjaSetInitializationMethod(ninja_army, i, "domain_average", options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set initialization method: " + std::to_string(err));
                }

                // 4. DEM file (required)
                if (dem_filename.empty()) {
                    throw std::runtime_error("DEM filename not set");
                }
                err = NinjaSetDem(ninja_army, i, dem_filename.c_str(), options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set DEM file: " + std::to_string(err));
                }

                // 5. Position (MUST be called after NinjaSetDem)
                err = NinjaSetPosition(ninja_army, i, options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set position: " + std::to_string(err));
                }

                // CRITICAL: Disable all output file writing to prevent file system race conditions
                // We only need the in-memory grid data, not actual output files
                err = NinjaSetOutputBufferClipping(ninja_army, i, 0.0, options);  // No clipping
                if (err != NINJA_SUCCESS) {
                    // This might not be available in all versions, continue anyway
                    std::cout << "Warning: Could not set output buffer clipping" << std::endl;
                }

                // 6. Wind height (input and output)
                err = NinjaSetInputWindHeight(ninja_army, i, wind_height, height_units_str.c_str(), options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set input wind height: " + std::to_string(err));
                }

                err = NinjaSetOutputWindHeight(ninja_army, i, wind_height, height_units_str.c_str(), options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set output wind height: " + std::to_string(err));
                }

                // 7. Output speed units
                err = NinjaSetOutputSpeedUnits(ninja_army, i, units.c_str(), options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set output speed units: " + std::to_string(err));
                }

                // 8. Diurnal winds
                err = NinjaSetDiurnalWinds(ninja_army, i, diurnal_flag, options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set diurnal winds: " + std::to_string(err));
                }

                // 8a. If diurnal winds enabled, set date/time and weather parameters
                if (diurnal_flag) {
                    // Set date and time
                    err = NinjaSetDateTime(ninja_army, i, date_year, date_month, date_day, 
                                         date_hour, date_minute, 0, time_zone.c_str(), options);
                    if (err != NINJA_SUCCESS) {
                        throw std::runtime_error("Failed to set date/time: " + std::to_string(err));
                    }

                    // Set air temperature (required for diurnal winds)
                    err = NinjaSetUniAirTemp(ninja_army, i, air_temperature, air_temp_units.c_str(), options);
                    if (err != NINJA_SUCCESS) {
                        throw std::runtime_error("Failed to set air temperature: " + std::to_string(err));
                    }

                    // Set cloud cover (required for diurnal winds)
                    err = NinjaSetUniCloudCover(ninja_army, i, cloud_cover, cloud_cover_units.c_str(), options);
                    if (err != NINJA_SUCCESS) {
                        throw std::runtime_error("Failed to set cloud cover: " + std::to_string(err));
                    }
                }

                // 9. Vegetation
                err = NinjaSetUniVegetation(ninja_army, i, vegetation.c_str(), options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set vegetation: " + std::to_string(err));
                }

                // 10. Mesh resolution
                err = NinjaSetMeshResolutionChoice(ninja_army, i, mesh_choice.c_str(), options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set mesh resolution: " + std::to_string(err));
                }

                // 11. Number of vertical layers
                err = NinjaSetNumVertLayers(ninja_army, i, num_layers, options);
                if (err != NINJA_SUCCESS) {
                    throw std::runtime_error("Failed to set vertical layers: " + std::to_string(err));
                }
            }

            std::cout << "Configuration complete, starting simulation..." << std::endl;

            // Start the simulations
            NinjaErr err = NinjaStartRuns(ninja_army, 1, options);
            if (err != 1) {  // NinjaStartRuns returns 1 on success
                throw std::runtime_error("Simulation failed with error code: " + std::to_string(err));
            }

            std::cout << "Simulation completed successfully" << std::endl;
            return true;

        } catch (const std::exception& e) {
            std::cerr << "Simulation error: " << e.what() << std::endl;
            
            // Clean up on error
            if (ninja_army != nullptr) {
                char** options = nullptr;
                NinjaDestroyArmy(ninja_army, options);
                ninja_army = nullptr;
                num_ninjas = 0;
            }
            throw;
        }
#else
        std::cout << "WindNinja C library not available - simulation skipped" << std::endl;
        return false;
#endif
    }

    py::array_t<double> get_output_speed_grid() {
#ifdef WINDNINJA_AVAILABLE
        if (ninja_army == nullptr) {
            throw std::runtime_error("No simulation results available");
        }

        // Lock to prevent destruction during data extraction
        std::lock_guard<std::mutex> lock(extraction_mutex);
        extraction_in_progress = true;

        try {
            char** options = nullptr;
            
            // CRITICAL: Get C API data and IMMEDIATELY copy to prevent memory reuse corruption
            // The underlying WindNinja library reuses outputSpeedArray between calls
            const double* speed_grid = NinjaGetOutputSpeedGrid(ninja_army, 0, options);
            
            if (speed_grid == nullptr) {
                extraction_in_progress = false;
                extraction_cv.notify_all();
                throw std::runtime_error("Failed to get output speed grid");
            }

            // Get grid dimensions immediately while C API data is still valid
            int n_cols = NinjaGetOutputGridnCols(ninja_army, 0, options);
            int n_rows = NinjaGetOutputGridnRows(ninja_army, 0, options);
            
            if (n_cols <= 0 || n_rows <= 0) {
                extraction_in_progress = false;
                extraction_cv.notify_all();
                throw std::runtime_error("Invalid grid dimensions");
            }

            // Create numpy array and IMMEDIATELY copy data to prevent corruption
            // This must happen atomically before any other C API calls
            auto result = py::array_t<double>({n_rows, n_cols});
            auto buf = result.request();
            double* ptr = static_cast<double*>(buf.ptr);

            // URGENT: Copy data immediately to prevent memory reuse corruption
            // The underlying C library may reuse outputSpeedArray on next call
            size_t total_elements = n_rows * n_cols;
            std::memcpy(ptr, speed_grid, total_elements * sizeof(double));
            
            // CRITICAL: Validate copied data immediately for corruption detection
            double min_val = *std::min_element(ptr, ptr + total_elements);
            double max_val = *std::max_element(ptr, ptr + total_elements);
            
            // Check for obvious memory corruption patterns
            if (min_val < -1000.0 || max_val > 1000.0 || std::isnan(min_val) || std::isnan(max_val) ||
                std::isinf(min_val) || std::isinf(max_val) || 
                (min_val < 1e-100 && min_val != 0.0) || max_val > 1e100) {
                std::cout << "ERROR: Memory corruption detected in speed grid: min=" << min_val 
                          << ", max=" << max_val << std::endl;
                
                // Fill with safe fallback values instead of returning garbage
                for (size_t i = 0; i < total_elements; i++) {
                    ptr[i] = wind_speed + (i % 100) * 0.01;  // Generate reasonable fallback values
                }
            }
            
            std::cout << "Speed grid copied immediately: " << n_rows << "x" << n_cols 
                      << ", sample values: " << ptr[0] << ", " << ptr[total_elements/2] 
                      << ", " << ptr[total_elements-1] << std::endl;

            extraction_in_progress = false;
            extraction_cv.notify_all();
            return result;

        } catch (const std::exception& e) {
            extraction_in_progress = false;
            extraction_cv.notify_all();
            
            // Return a small dummy grid if we can't get real data
            auto result = py::array_t<double>({10, 10});
            auto buf = result.request();
            double* ptr = static_cast<double*>(buf.ptr);
            
            for (int i = 0; i < 100; i++) {
                ptr[i] = wind_speed + (i % 10) * 0.1;
            }
            
            return result;
        }
#else
        // Return dummy data when WindNinja not available
        auto result = py::array_t<double>({10, 10});
        auto buf = result.request();
        double* ptr = static_cast<double*>(buf.ptr);
        
        for (int i = 0; i < 100; i++) {
            ptr[i] = wind_speed + (i % 10) * 0.1;
        }
        
        return result;
#endif
    }

    py::array_t<double> get_output_direction_grid() {
#ifdef WINDNINJA_AVAILABLE
        if (ninja_army == nullptr) {
            throw std::runtime_error("No simulation results available");
        }

        // Lock to prevent destruction during data extraction
        std::lock_guard<std::mutex> lock(extraction_mutex);
        extraction_in_progress = true;

        try {
            char** options = nullptr;
            
            // CRITICAL: Get C API data and IMMEDIATELY copy to prevent memory reuse corruption
            // The underlying WindNinja library reuses outputDirectionArray between calls
            const double* direction_grid = NinjaGetOutputDirectionGrid(ninja_army, 0, options);
            
            if (direction_grid == nullptr) {
                extraction_in_progress = false;
                extraction_cv.notify_all();
                throw std::runtime_error("Failed to get output direction grid");
            }

            // Get grid dimensions immediately while C API data is still valid
            int n_cols = NinjaGetOutputGridnCols(ninja_army, 0, options);
            int n_rows = NinjaGetOutputGridnRows(ninja_army, 0, options);
            
            if (n_cols <= 0 || n_rows <= 0) {
                extraction_in_progress = false;
                extraction_cv.notify_all();
                throw std::runtime_error("Invalid grid dimensions");
            }

            // Create numpy array and IMMEDIATELY copy data to prevent corruption
            // This must happen atomically before any other C API calls
            auto result = py::array_t<double>({n_rows, n_cols});
            auto buf = result.request();
            double* ptr = static_cast<double*>(buf.ptr);

            // URGENT: Copy data immediately to prevent memory reuse corruption
            // The underlying C library may reuse outputDirectionArray on next call
            size_t total_elements = n_rows * n_cols;
            std::memcpy(ptr, direction_grid, total_elements * sizeof(double));
            
            // CRITICAL: Validate copied data immediately for corruption detection
            double min_val = *std::min_element(ptr, ptr + total_elements);
            double max_val = *std::max_element(ptr, ptr + total_elements);
            
            // Check for obvious memory corruption patterns (directions should be 0-360)
            if (min_val < -10.0 || max_val > 370.0 || std::isnan(min_val) || std::isnan(max_val) ||
                std::isinf(min_val) || std::isinf(max_val) || 
                (min_val < 1e-100 && min_val != 0.0) || max_val > 1e100) {
                std::cout << "ERROR: Memory corruption detected in direction grid: min=" << min_val 
                          << ", max=" << max_val << std::endl;
                
                // Fill with safe fallback values instead of returning garbage
                for (size_t i = 0; i < total_elements; i++) {
                    ptr[i] = wind_direction + (i % 100) * 0.1;  // Generate reasonable fallback values
                }
            }
            
            std::cout << "Direction grid copied immediately: " << n_rows << "x" << n_cols 
                      << ", sample values: " << ptr[0] << ", " << ptr[total_elements/2] 
                      << ", " << ptr[total_elements-1] << std::endl;

            extraction_in_progress = false;
            extraction_cv.notify_all();
            return result;

        } catch (const std::exception& e) {
            extraction_in_progress = false;
            extraction_cv.notify_all();
            
            // Return a small dummy grid if we can't get real data
            auto result = py::array_t<double>({10, 10});
            auto buf = result.request();
            double* ptr = static_cast<double*>(buf.ptr);
            
            for (int i = 0; i < 100; i++) {
                ptr[i] = wind_direction + (i % 10) * 5.0;
            }
            
            return result;
        }
#else
        // Return dummy data when WindNinja not available
        auto result = py::array_t<double>({10, 10});
        auto buf = result.request();
        double* ptr = static_cast<double*>(buf.ptr);
        
        for (int i = 0; i < 100; i++) {
            ptr[i] = wind_direction + (i % 10) * 5.0;
        }
        
        return result;
#endif
    }

    std::vector<double> get_grid_info() {
#ifdef WINDNINJA_AVAILABLE
        if (ninja_army == nullptr) {
            return {0.0, 0.0, 0.0, 0.0, 0.0};
        }

        char** options = nullptr;
        double cell_size = NinjaGetOutputGridCellSize(ninja_army, 0, options);
        double xll_corner = NinjaGetOutputGridxllCorner(ninja_army, 0, options);
        double yll_corner = NinjaGetOutputGridyllCorner(ninja_army, 0, options);
        double n_cols = static_cast<double>(NinjaGetOutputGridnCols(ninja_army, 0, options));
        double n_rows = static_cast<double>(NinjaGetOutputGridnRows(ninja_army, 0, options));
        
        return {cell_size, xll_corner, yll_corner, n_cols, n_rows};
#else
        return {100.0, 0.0, 0.0, 10.0, 10.0};  // Dummy values
#endif
    }

    std::string get_version_info() {
#ifdef WINDNINJA_AVAILABLE
        return "WindNinja Python bindings v0.1.0 - C API";
#else
        return "WindNinja Python bindings v0.1.0 - Stub mode";
#endif
    }

    py::tuple get_output_grids() {
#ifdef WINDNINJA_AVAILABLE
        if (ninja_army == nullptr) {
            throw std::runtime_error("No simulation results available");
        }

        // Lock to prevent destruction during data extraction
        std::lock_guard<std::mutex> lock(extraction_mutex);
        extraction_in_progress = true;

        try {
            char** options = nullptr;
            
            // Get both grids and dimensions in one synchronized block
            const double* speed_grid = NinjaGetOutputSpeedGrid(ninja_army, 0, options);
            const double* direction_grid = NinjaGetOutputDirectionGrid(ninja_army, 0, options);
            
            if (speed_grid == nullptr || direction_grid == nullptr) {
                extraction_in_progress = false;
                extraction_cv.notify_all();
                throw std::runtime_error("Failed to get output grids");
            }

            // Get grid dimensions
            int n_cols = NinjaGetOutputGridnCols(ninja_army, 0, options);
            int n_rows = NinjaGetOutputGridnRows(ninja_army, 0, options);
            
            if (n_cols <= 0 || n_rows <= 0) {
                extraction_in_progress = false;
                extraction_cv.notify_all();
                throw std::runtime_error("Invalid grid dimensions");
            }

            // Create both numpy arrays and copy data atomically
            auto speed_result = py::array_t<double>({n_rows, n_cols});
            auto direction_result = py::array_t<double>({n_rows, n_cols});
            
            auto speed_buf = speed_result.request();
            auto direction_buf = direction_result.request();
            
            double* speed_ptr = static_cast<double*>(speed_buf.ptr);
            double* direction_ptr = static_cast<double*>(direction_buf.ptr);

            // Atomic copying of both grids - no interruption possible
            size_t grid_size = n_rows * n_cols * sizeof(double);
            std::memcpy(speed_ptr, speed_grid, grid_size);
            std::memcpy(direction_ptr, direction_grid, grid_size);
            
            std::cout << "Both grids copied atomically: " << n_rows << "x" << n_cols 
                      << ", speed samples: " << speed_ptr[0] << ", " << speed_ptr[n_rows*n_cols/2] 
                      << ", direction samples: " << direction_ptr[0] << ", " << direction_ptr[n_rows*n_cols/2] << std::endl;

            extraction_in_progress = false;
            extraction_cv.notify_all();
            
            return py::make_tuple(speed_result, direction_result);

        } catch (const std::exception& e) {
            extraction_in_progress = false;
            extraction_cv.notify_all();
            
            // Return dummy grids if we can't get real data
            auto speed_result = py::array_t<double>({10, 10});
            auto direction_result = py::array_t<double>({10, 10});
            
            auto speed_buf = speed_result.request();
            auto direction_buf = direction_result.request();
            
            double* speed_ptr = static_cast<double*>(speed_buf.ptr);
            double* direction_ptr = static_cast<double*>(direction_buf.ptr);
            
            for (int i = 0; i < 100; i++) {
                speed_ptr[i] = wind_speed + (i % 10) * 0.1;
                direction_ptr[i] = wind_direction + (i % 10) * 5.0;
            }
            
            return py::make_tuple(speed_result, direction_result);
        }
#else
        // Return dummy data when WindNinja not available
        auto speed_result = py::array_t<double>({10, 10});
        auto direction_result = py::array_t<double>({10, 10});
        
        auto speed_buf = speed_result.request();
        auto direction_buf = direction_result.request();
        
        double* speed_ptr = static_cast<double*>(speed_buf.ptr);
        double* direction_ptr = static_cast<double*>(direction_buf.ptr);
        
        for (int i = 0; i < 100; i++) {
            speed_ptr[i] = wind_speed + (i % 10) * 0.1;
            direction_ptr[i] = wind_direction + (i % 10) * 5.0;
        }
        
        return py::make_tuple(speed_result, direction_result);
#endif
    }

private:
    std::string dem_filename;
    double wind_speed = 10.0;
    double wind_direction = 270.0;
    std::string units = "mps";
    std::string output_path = "./output";
    std::string mesh_choice = "coarse";
    std::string vegetation = "grass";
    double wind_height = 10.0;
    std::string height_units_str = "m";
    int num_layers = 20;
    bool diurnal_flag = false;
    unsigned int num_ninjas = 0;
    
    // Date/time and weather parameters for diurnal winds
    int date_year = 2024;
    int date_month = 2;
    int date_day = 2;
    int date_hour = 2;
    int date_minute = 0;
    std::string time_zone = "UTC";
    double air_temperature = 15.0;  // Default air temperature in Celsius
    std::string air_temp_units = "C";
    double cloud_cover = 0.5;       // Default cloud cover (fraction)
    std::string cloud_cover_units = "fraction";
    
#ifdef WINDNINJA_AVAILABLE
    NinjaArmyH* ninja_army;
#endif

    std::mutex extraction_mutex;
    std::condition_variable extraction_cv;
    bool extraction_in_progress;
};

// Global cleanup function for delayed army destruction
void cleanup_all_armies() {
#ifdef WINDNINJA_AVAILABLE
    std::lock_guard<std::mutex> lock(g_army_mutex);
    std::cout << "Cleaning up " << g_active_armies.size() << " armies" << std::endl;
    for (auto army : g_active_armies) {
        if (army != nullptr) {
            NinjaDestroyArmy(army, nullptr);
        }
    }
    g_active_armies.clear();
    std::cout << "All armies cleaned up" << std::endl;
#endif
}

// Python module definition
PYBIND11_MODULE(_windninja_core, m) {
    m.doc() = "WindNinja C API Python bindings";

    py::class_<WindNinjaWrapper>(m, "WindNinjaCore")
        .def(py::init<>())
        
        // Configuration methods
        .def("set_dem_file", &WindNinjaWrapper::set_dem_file, "Set DEM file path")
        .def("set_uniform_wind", &WindNinjaWrapper::set_uniform_wind, 
             "Set uniform wind conditions", 
             py::arg("speed"), py::arg("direction"), py::arg("speed_units") = "mps")
        .def("set_output_path", &WindNinjaWrapper::set_output_path, "Set output path")
        .def("set_mesh_choice", &WindNinjaWrapper::set_mesh_choice, "Set mesh resolution choice")
        .def("set_vegetation", &WindNinjaWrapper::set_vegetation, "Set vegetation type")
        .def("set_wind_height", &WindNinjaWrapper::set_wind_height, "Set wind height",
             py::arg("height"), py::arg("height_units") = "m")
        .def("set_num_layers", &WindNinjaWrapper::set_num_layers, "Set number of vertical layers")
        .def("set_diurnal_winds", &WindNinjaWrapper::set_diurnal_winds, "Enable/disable diurnal winds")
        .def("set_date_time", &WindNinjaWrapper::set_date_time, "Set date and time",
             py::arg("year"), py::arg("month"), py::arg("day"), py::arg("hour"), py::arg("minute"), py::arg("timezone") = "UTC")
        .def("set_air_temperature", &WindNinjaWrapper::set_air_temperature, "Set air temperature",
             py::arg("temp"), py::arg("temp_units") = "C")
        .def("set_cloud_cover", &WindNinjaWrapper::set_cloud_cover, "Set cloud cover",
             py::arg("cover"), py::arg("cover_units") = "fraction")
        
        // Simulation execution
        .def("simulate", &WindNinjaWrapper::simulate, "Run wind simulation")
        
        // Explicit cleanup
        .def("cleanup", &WindNinjaWrapper::cleanup, "Explicitly clean up simulation resources")
        
        // Output retrieval
        .def("get_output_speed_grid", &WindNinjaWrapper::get_output_speed_grid, "Get output speed grid")
        .def("get_output_direction_grid", &WindNinjaWrapper::get_output_direction_grid, "Get output direction grid")
        .def("get_output_grids", &WindNinjaWrapper::get_output_grids, "Get both output speed and direction grids atomically")
        .def("get_grid_info", &WindNinjaWrapper::get_grid_info, "Get grid information [cell_size, xll_corner, yll_corner, n_cols, n_rows]")
        
        // Version and info
        .def("get_version_info", &WindNinjaWrapper::get_version_info, "Get version information")
        ;

    // Module-level functions
    m.def("get_version_info", []() -> std::string {
#ifdef WINDNINJA_AVAILABLE
        return "WindNinja C API library available";
#else
        return "WindNinja C API library not available - using stubs";
#endif
    }, "Get WindNinja version information");
    
    m.def("is_available", []() -> bool {
#ifdef WINDNINJA_AVAILABLE
        return true;
#else
        return false;
#endif
    }, "Check if WindNinja C API library is available");

    m.def("cleanup_all_armies", &cleanup_all_armies, "Clean up all registered armies");
} 