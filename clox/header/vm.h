//
// Created by bekyiu on 2023/2/24.
//

#ifndef CLOX_VM_H
#define CLOX_VM_H

#include "chunk.h"
#include "value.h"

#define STACK_MAX 256

typedef struct {
    Chunk *chunk;
    // 指向下一条需要执行的指令(opcode)所在的位置
    uint8_t *ip;
    // 虚拟机栈
    Value stack[STACK_MAX];
    // 指向栈顶元素的下一个位置
    Value *stackTop;
    // lox对象链表
    Obj *objects;
} VM;

typedef enum {
    INTERPRET_OK,
    INTERPRET_COMPILE_ERROR,
    INTERPRET_RUNTIME_ERROR,
} InterpretResult;

extern VM vm;

void initVM();

void freeVM();

InterpretResult interpret(const char *source);

#endif //CLOX_VM_H
