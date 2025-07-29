cmake_minimum_required(VERSION 3.15...3.30)
project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)

find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development.Module)
execute_process(
  COMMAND "${Python_EXECUTABLE}"
          "-c" "from jax import ffi; print(ffi.include_dir())"
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE XLA_DIR)
message(STATUS "XLA include directory: ${XLA_DIR}")

find_package(nanobind CONFIG REQUIRED)

set(
  CUDA_PROJECTS
  "wkv4"
  "wkv7"
)

# Include the CUDA extensions if possible
include(CheckLanguage)
check_language(CUDA)

if(CMAKE_CUDA_COMPILER)
  enable_language(CUDA)
  find_package(CUDAToolkit REQUIRED)

  foreach(PROJECT ${CUDA_PROJECTS})
    add_library("_${PROJECT}" SHARED "src/jaxrwkvkernel/cuda/${PROJECT}.cu")
    target_compile_options("_${PROJECT}" PRIVATE $<$<COMPILE_LANGUAGE:CUDA>:
                         --use_fast_math
		         -extra-device-vectorization
			 -O3
                         >)
    set_target_properties("_${PROJECT}" PROPERTIES POSITION_INDEPENDENT_CODE ON CUDA_STANDARD 17)
    target_include_directories("_${PROJECT}" PUBLIC ${XLA_DIR})
    install(TARGETS "_${PROJECT}" LIBRARY DESTINATION ${SKBUILD_PROJECT_NAME})
  endforeach()
endif()
