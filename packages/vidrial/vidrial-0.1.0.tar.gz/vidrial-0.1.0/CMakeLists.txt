cmake_minimum_required(VERSION 3.18)
project(cuda_tprod LANGUAGES CXX CUDA)

# Set CUDA architectures first
set(CMAKE_CUDA_ARCHITECTURES 80)

# Set language standards
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CUDA_STANDARD 20)

# CUDA flags
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} --std=c++20 -extended-lambda --expt-relaxed-constexpr -w -lineinfo -Xcompiler -ftemplate-backtrace-limit=1000")

# Find CUDA
find_package(CUDA REQUIRED)

# Set CUTLASS include path
set(CUTLASS_INCLUDE_DIR ${CMAKE_SOURCE_DIR}/cutlass/include/cutlass)
if(NOT EXISTS ${CUTLASS_INCLUDE_DIR})
    message(FATAL_ERROR "CUTLASS include directory not found at ${CUTLASS_INCLUDE_DIR}")
endif()

# Download and build Google Test
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
)
FetchContent_MakeAvailable(googletest)

# Header-only library target
add_library(cuda_tprod_lib INTERFACE)
target_include_directories(cuda_tprod_lib INTERFACE
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/mosaic
    ${CMAKE_SOURCE_DIR}/mosaic/mosaics
    ${CMAKE_SOURCE_DIR}/mosaic/utils
    ${CMAKE_SOURCE_DIR}/kernels
    ${CMAKE_SOURCE_DIR}/kernels/add_one
    ${CMAKE_SOURCE_DIR}/kernels/copy
    ${CMAKE_SOURCE_DIR}/kernels/mma
    ${CMAKE_SOURCE_DIR}/kernels/sympow
    ${CMAKE_SOURCE_DIR}/kernels/sympow_mma
    ${CMAKE_SOURCE_DIR}/kernels/tprod
    ${CMAKE_SOURCE_DIR}/cutlass/include
)

# Enable testing
enable_testing()

# Individual test executables
set(TEST_SOURCES
    mosaic/mosaics/tests/mma_mosaic_test.cu
    mosaic/mosaics/tests/tprod_mosaic_test.cu
    mosaic/mosaics/tests/copy_mosaic_test.cu
    mosaic/mosaics/tests/sympow_mosaic_test.cu
    mosaic/mosaics/tests/sympow_mma_mosaic_test.cu
    mosaic/mosaics/tests/add_one_mosaic_test.cu
    mosaic/mosaics/tests/swizzle_test.cu
    mosaic/utils/tests/utils_test.cu
    mosaic/utils/tests/reduce_test.cu
    mosaic/utils/tests/ldsm_test.cu
    mosaic/utils/tests/tprod_test.cu
    kernels/sympow/test.cu
    kernels/sympow_bwd/test.cu
)

# Create individual test targets
foreach(TEST_SOURCE ${TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST_SOURCE} NAME_WE)
    get_filename_component(TEST_DIR ${TEST_SOURCE} DIRECTORY)
    get_filename_component(TEST_DIR_NAME ${TEST_DIR} NAME)
    set(TARGET_NAME "${TEST_DIR_NAME}_${TEST_NAME}")
    add_executable(${TARGET_NAME} ${TEST_SOURCE})
    target_link_libraries(${TARGET_NAME} PRIVATE
        cuda_tprod_lib
        GTest::gtest_main
        GTest::gmock_main
        ${CUDA_LIBRARIES}
    )
    add_test(NAME ${TARGET_NAME} COMMAND ${TARGET_NAME})
endforeach()

# Combined test executable
add_executable(tests ${TEST_SOURCES})
target_link_libraries(tests PRIVATE
    cuda_tprod_lib
    GTest::gtest_main
    GTest::gmock_main
    ${CUDA_LIBRARIES}
)
add_test(NAME tests COMMAND tests)

# Add tutorial executable
add_executable(dynamic_vs_static_mosaics tutorials/dynamic_vs_static_mosaics.cu)
target_link_libraries(dynamic_vs_static_mosaics PRIVATE
    cuda_tprod_lib
    ${CUDA_LIBRARIES}
)
set_target_properties(dynamic_vs_static_mosaics PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
)
