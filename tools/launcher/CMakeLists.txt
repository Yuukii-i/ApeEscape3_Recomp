cmake_minimum_required(VERSION 3.20)
project(ape3_launcher_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

set(SDL_SHARED OFF CACHE BOOL "" FORCE)
set(SDL_STATIC ON CACHE BOOL "" FORCE)
set(SDL_TEST_LIBRARY OFF CACHE BOOL "" FORCE)
set(SDL_INSTALL OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    SDL3
    GIT_REPOSITORY "https://github.com/libsdl-org/SDL.git"
    GIT_TAG "release-3.2.28"
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(SDL3)

FetchContent_Declare(
    imgui
    GIT_REPOSITORY https://github.com/ocornut/imgui.git
    GIT_TAG "v1.92.7-docking"
    GIT_SHALLOW TRUE
)
FetchContent_GetProperties(imgui)
if(NOT imgui_POPULATED)
    FetchContent_Populate(imgui)
endif()

add_library(imgui STATIC
    ${imgui_SOURCE_DIR}/imgui.cpp
    ${imgui_SOURCE_DIR}/imgui_draw.cpp
    ${imgui_SOURCE_DIR}/imgui_tables.cpp
    ${imgui_SOURCE_DIR}/imgui_widgets.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_sdl3.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_sdlrenderer3.cpp
)
target_include_directories(imgui PUBLIC
    ${imgui_SOURCE_DIR}
    ${imgui_SOURCE_DIR}/backends
)
target_link_libraries(imgui PUBLIC SDL3::SDL3)

add_library(ape3_launcher_core STATIC
    settings.h
    settings.cpp
)
target_include_directories(ape3_launcher_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(test_settings
    test_settings.cpp
)
target_link_libraries(test_settings PRIVATE ape3_launcher_core)

if(WIN32)
    add_executable(ape3_launcher WIN32
        main.cpp
        ui.h
        ui.cpp
        process.h
        process.cpp
    )
else()
    add_executable(ape3_launcher
        main.cpp
        ui.h
        ui.cpp
        process.h
        process.cpp
    )
endif()

target_link_libraries(ape3_launcher PRIVATE
    ape3_launcher_core
    imgui
    SDL3::SDL3
)
