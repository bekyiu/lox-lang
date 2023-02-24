cmake_minimum_required(VERSION 3.19)
project(clox C)

set(CMAKE_C_STANDARD 99)

# 设定头文件路径
include_directories(./header)

# 查找指定目录下的所有源文件
aux_source_directory(./src DIR_SRC)

add_executable(clox main.c ${DIR_SRC})



