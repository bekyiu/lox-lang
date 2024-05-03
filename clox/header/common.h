#ifndef CLOX_COMMON_H
#define CLOX_COMMON_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 打印编译后的反编译代码
#define DEBUG_PRINT_CODE

// 每条指令执行前进行反编译, 并打印
#define DEBUG_TRACE_EXECUTION

// 开启后 会尽可能的触发gc
#define DEBUG_STRESS_GC

#define DEBUG_LOG_GC

#define UINT8_COUNT (UINT8_MAX + 1)

#endif //CLOX_COMMON_H
