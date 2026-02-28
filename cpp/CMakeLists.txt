cmake_minimum_required(VERSION 3.10)
project(edlora)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Create edlora library
add_library(edlora STATIC edlora.cpp)
target_include_directories(edlora PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Example executable to test standard linux build
add_executable(edlora_test ../examples/test_linux.cpp)
target_link_libraries(edlora_test edlora)

# Simulate flight executable
add_executable(simulate_flight ../examples/simulate_flight.cpp)
target_link_libraries(simulate_flight edlora)

# Comprehensive Unit Tests
add_executable(test_protocol ../tests/cpp/test_protocol.cpp)
target_link_libraries(test_protocol edlora)
