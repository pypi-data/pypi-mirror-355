cmake_minimum_required(VERSION 3.18)
project(cuMatfuse LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 14)
enable_language(CUDA)

find_package(pybind11 REQUIRED)
pybind11_add_module(cuMatfuse src/cuMatfuse_bindings.cpp src/cuMatfuse_kernel.cu)
target_link_libraries(cuMatfuse PRIVATE cuda)

# Explicitly add CUDA include directory for both CXX and CUDA
include_directories(include)
include_directories(/usr/local/cuda-12.9/include)

add_executable(cuMatfuse_demo src/main.cpp src/cuMatfuse_kernel.cu)

# Link CUDA runtime explicitly (optional but safe)
target_link_libraries(cuMatfuse_demo cuda)

