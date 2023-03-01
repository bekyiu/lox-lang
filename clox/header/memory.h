#ifndef CLOX_MEMORY_H
#define CLOX_MEMORY_H

#include "common.h"

#define GROW_CAPACITY(capacity) \
    ((capacity) < 8 ? 8 : (capacity) * 2)

#define GROW_ARRAY(type, pointer, oldCount, newCount) \
    (type*)reallocate(pointer, sizeof(type) * (oldCount), \
        sizeof(type) * (newCount))

#define FREE_ARRAY(type, pointer, oldCount) \
    reallocate(pointer, sizeof(type) * (oldCount), 0)

#define ALLOCATE(type, size) \
    (type*)reallocate(NULL, 0, sizeof(type) * (size))

/**
 * 分配内存, 释放内存, 以及改变现有分配的大小
 *
 * oldSize	    newSize	                Operation
 * 0            Non‑zero	            分配新块
 * Non‑zero	    0	                    释放已分配内存
 * Non‑zero	    Smaller than oldSize	收缩已分配内存
 * Non‑zero	    Larger than oldSize	    增加已分配内存
 *
 * @param pointer 内存首地址
 * @param oldSize 旧的内存大小
 * @param newSize 新的内存大小
 * @return
 */
void *reallocate(void *pointer, size_t oldSize, size_t newSize);

#endif //CLOX_MEMORY_H
