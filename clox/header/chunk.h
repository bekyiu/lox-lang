#ifndef CLOX_CHUNK_H
#define CLOX_CHUNK_H

#include "common.h"
#include "value.h"

typedef enum {
    OP_CONSTANT,
    OP_ADD,
    OP_SUBTRACT,
    OP_MULTIPLY,
    OP_DIVIDE,
    OP_NEGATE,
    OP_RETURN,
} OpCode;

// 指令数组
typedef struct {
    // 字节码数组
    int count;
    int capacity;
    uint8_t *code;
    // 行号数组 记录每个字节码是被哪一行源代码编译出来的
    int *lines;
    // 常量池
    ValueArray constants;
} Chunk;

void initChunk(Chunk *chunk);

void writeChunk(Chunk *chunk, uint8_t byte, int line);

void freeChunk(Chunk *chunk);

/**
 * 向常量池添加常量
 * @param chunk
 * @param value
 * @return 返回新添加的常量在常量池中的索引
 */
int addConstant(Chunk *chunk, Value value);

#endif //CLOX_CHUNK_H
