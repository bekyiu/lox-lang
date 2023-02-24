cmake_minimum_required(VERSION 3.19)
project(clox C)

set(CMAKE_C_STANDARD 99)

add_executable(clox main.c header/common.h header/chunk.h src/chunk.c header/memory.h src/memory.c header/debug.h src/debug.c header/value.h src/value.c)