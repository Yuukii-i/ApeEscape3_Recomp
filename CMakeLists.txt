cmake_minimum_required(VERSION 3.21)

project(ApeEscape3_Recomp LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Ensure SSE4.1 intrinsics used by PS2 vector/runtime macros are enabled on GCC/Clang
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-msse4.1)
    if(WIN32)
        add_compile_options("-Wa,-mbig-obj")
    endif()
endif()

# Configure PS2Recomp submodules: enable runtime and IOP, disable standalone tools/tests by default
set(PS2X_BUILD_RUNTIME ON CACHE BOOL "Build ps2xRuntime")
set(PS2X_BUILD_RECOMP OFF CACHE BOOL "Build ps2xRecomp")
set(PS2X_BUILD_ANALYZER OFF CACHE BOOL "Build ps2xAnalyzer")
set(PS2X_BUILD_TEST OFF CACHE BOOL "Build ps2xTest")
set(PS2X_BUILD_STUDIO OFF CACHE BOOL "Build ps2xStudio")

# Add PS2Recomp subdirectory
add_subdirectory(PS2Recomp)

# Ensure ps2xRuntime alias exists for the runtime target
if(TARGET ps2_runtime AND NOT TARGET ps2xRuntime)
    add_library(ps2xRuntime ALIAS ps2_runtime)
endif()

# Collect all C++ source files from recomp_source
file(GLOB_RECURSE RECOMP_SOURCES CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/recomp_source/*.cpp"
)

# PERF-IV: optionally link a prebuilt clang-cl build of recomp_source (tools/build_clang_recomp.bat) instead of compiling it here
set(RECOMP_CLANG_LIB "" CACHE FILEPATH "Prebuilt clang-cl recomp_source static library (empty = build recomp_source with the main compiler)")
if(RECOMP_CLANG_LIB AND EXISTS "${RECOMP_CLANG_LIB}")
    message(STATUS "recomp_source: using prebuilt clang-cl library ${RECOMP_CLANG_LIB}")
    add_library(recomp_source STATIC IMPORTED GLOBAL)
    set_target_properties(recomp_source PROPERTIES
        IMPORTED_LOCATION "${RECOMP_CLANG_LIB}"
        INTERFACE_INCLUDE_DIRECTORIES "${CMAKE_CURRENT_SOURCE_DIR}/recomp_source;${CMAKE_CURRENT_SOURCE_DIR}/PS2Recomp/ps2xRuntime/include"
        INTERFACE_LINK_LIBRARIES ps2xRuntime)
else()
# Compile recomp_source files into a static library
add_library(recomp_source STATIC ${RECOMP_SOURCES})

# Target include directories
target_include_directories(recomp_source PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/recomp_source"
    "${CMAKE_CURRENT_SOURCE_DIR}/PS2Recomp/ps2xRuntime/include"
)

# Link against the ps2xRuntime library
target_link_libraries(recomp_source PUBLIC ps2xRuntime)

# Compiler options for large generated codebases
if(MSVC)
    target_compile_options(recomp_source PRIVATE /bigobj /FS)
    # PERF-IS: recomp_source never got the runtime's fast flags (EnableFastReleaseMode): only /O2 /Ob2. Add the safe subset
    # (NOT /GL: LTCG over 23k functions; NOT /fp:fast: guest FPU semantics). Experiment: guest code is IPC-healthy but instruction-bound.
    target_compile_options(recomp_source PRIVATE $<$<CONFIG:Release>:/arch:AVX2 /GS- /Gy /Gw /GF /Oi /Qspectre->)
elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(recomp_source PRIVATE -msse4.1 "-Wa,-mbig-obj")
endif()

# Enable unity build support to accelerate compilation of the large number of source files
option(RECOMP_ENABLE_UNITY_BUILD "Build recomp_source with CMake unity build" ON)
set(RECOMP_UNITY_BUILD_BATCH_SIZE 32 CACHE STRING "Unity build batch size for recomp_source")
if(RECOMP_ENABLE_UNITY_BUILD)
    set_target_properties(recomp_source PROPERTIES
        UNITY_BUILD ON
        UNITY_BUILD_BATCH_SIZE "${RECOMP_UNITY_BUILD_BATCH_SIZE}"
    )
endif()

endif() # RECOMP_CLANG_LIB

# Aliases for convenience
add_library(recomp_game ALIAS recomp_source)
add_library(ApeEscape3_recomp ALIAS recomp_source)

if(TARGET ps2EntryRunner)
    target_compile_definitions(ps2EntryRunner PRIVATE PS2X_HAS_RECOMPILED_GAME=1)
    if(MSVC)
        target_link_options(ps2EntryRunner PRIVATE "/FORCE:MULTIPLE")
    elseif(MINGW OR (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang" AND WIN32))
        # -Wl,--allow-multiple-definition removed
    endif()
    target_link_libraries(ps2EntryRunner PRIVATE -Wl,--start-group recomp_source ps2xRuntime -Wl,--end-group)
endif()
