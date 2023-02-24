//
// Created by bekyiu on 2023/2/24.
//

#ifndef CLOX_VM_H
#define CLOX_VM_H

#include "chunk.h"

typedef struct {
    Chunk *chunk;
    // 指向下一条需要执行的指令(opcode)所在的位置
    uint8_t *ip;
} VM;

typedef enum {
    INTERPRET_OK,
    INTERPRET_COMPILE_ERROR,
    INTERPRET_RUNTIME_ERROR
} InterpretResult;

void initVM();

void freeVM();

InterpretResult interpret(Chunk *chunk);

#endif //CLOX_VM_H
