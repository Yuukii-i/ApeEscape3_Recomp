# PERF-IV: standalone clang-cl build of the generated guest code (recomp_source) into one static lib.
# The main (MSVC) tree links it instead of its own recomp_source when configured with -DRECOMP_CLANG_LIB=<path to this lib>.
cmake_minimum_required(VERSION 3.21)
project(recomp_clang LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreadedDLL") # /MD, same as the main tree

get_filename_component(REPO "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
file(GLOB_RECURSE RECOMP_SOURCES CONFIGURE_DEPENDS "${REPO}/recomp_source/*.cpp")
if(NOT RECOMP_SOURCES)
    message(FATAL_ERROR "No sources in ${REPO}/recomp_source - is the folder in place?")
endif()

add_library(recomp_source_clang STATIC ${RECOMP_SOURCES})
target_include_directories(recomp_source_clang PRIVATE
    "${REPO}/recomp_source"
    "${REPO}/PS2Recomp/ps2xRuntime/include"
    "${REPO}/PS2Recomp/ps2xRuntime/src/lib/Kernel"
    "${REPO}/build/_deps/raylib-src/src"
    "${REPO}/build/_deps/raylib-src/src/external/glfw/include"
    "${REPO}/PS2Recomp/ps2xIOP/include"
)
# SYSTEM-ish include for ffmpeg headers as in the main tree
target_compile_options(recomp_source_clang PRIVATE "-imsvc${REPO}/build/ThirdParty/ffmpeg-prefix/src/ffmpeg_external/include")
target_compile_definitions(recomp_source_clang PRIVATE
    GRAPHICS_API_OPENGL_33 PLATFORM_DESKTOP PS2X_ENABLE_IOP_RPC_TRACE=1 PS2_RUNTIME_LOGS=1 WIN32 _WINDOWS NDEBUG)
# Same flag set as the MSVC tree (Task IS) plus: no FMA contraction (guest FPU must round after every op), no warnings noise.
target_compile_options(recomp_source_clang PRIVATE "/FI${CMAKE_CURRENT_SOURCE_DIR}/clang_abi_fix.h") # PERF-JC
target_compile_options(recomp_source_clang PRIVATE /bigobj /arch:AVX2 /GS- /Gy /Gw /Oi /EHsc -Wno-everything -ffp-contract=off)
# Variant experiments: -DRECOMP_CLANG_EXTRA_FLAGS="-O3;-march=znver3" (semicolon list) and -DRECOMP_CLANG_LIB_NAME=<name>
set(RECOMP_CLANG_EXTRA_FLAGS "" CACHE STRING "Extra clang-cl flags (semicolon separated)")
if(RECOMP_CLANG_EXTRA_FLAGS)
    target_compile_options(recomp_source_clang PRIVATE ${RECOMP_CLANG_EXTRA_FLAGS})
endif()
set_target_properties(recomp_source_clang PROPERTIES UNITY_BUILD ON UNITY_BUILD_BATCH_SIZE 32)
