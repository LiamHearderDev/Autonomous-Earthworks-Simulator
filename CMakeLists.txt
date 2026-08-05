cmake_minimum_required(VERSION 3.15)

project(gz-chrono-loader LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(gz-plugin REQUIRED COMPONENTS all)
find_package(gz-physics REQUIRED)

add_executable(gz-chrono-loader gz-chrono-loader.cpp)

target_link_libraries(gz-chrono-loader
    gz-plugin::loader
    gz-physics::gz-physics
)