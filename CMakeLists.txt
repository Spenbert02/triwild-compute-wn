cmake_minimum_required(VERSION 3.10)
project(TriWildComputeWn)

# Use C++17 for modern filesystem support (great for directory iteration)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# dependencies
add_subdirectory(external/MshIO)
set(EIGEN3_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external/eigen")
add_subdirectory(external/eigen)

# Define the executable and its source files
add_executable(compute_wn src/compute_wn.cpp)
target_link_libraries(compute_wn PRIVATE mshio::mshio Eigen3::Eigen)
target_include_directories(compute_wn PRIVATE include)

find_package(OpenMP REQUIRED)
if(OpenMP_CXX_FOUND)
    target_link_libraries(compute_wn PUBLIC OpenMP::OpenMP_CXX)
endif()

# Optimization: Ensure we build in Release mode by default for speed
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()