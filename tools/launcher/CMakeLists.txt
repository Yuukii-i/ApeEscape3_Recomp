cmake_minimum_required(VERSION 3.20)
project(ape3_launcher_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(ape3_launcher_core STATIC
    settings.h
    settings.cpp
)
target_include_directories(ape3_launcher_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(test_settings
    test_settings.cpp
)
target_link_libraries(test_settings PRIVATE ape3_launcher_core)
