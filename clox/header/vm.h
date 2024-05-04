//
// Created by bekyiu on 2023/2/24.
//

#ifndef CLOX_VM_H
#define CLOX_VM_H

#include "chunk.h"
#include "value.h"
#include "table.h"
#include "object.h"

#define FRAMES_MAX 64
#define STACK_MAX (FRAMES_MAX * UINT8_COUNT)

typedef struct {
    // 被调函数
    ObjClosure *closure;
    // 被调函数运行的ip
    uint8_t *ip;
    // 属于背调函数栈的开始
    Value *slots;
} CallFrame;

typedef struct {
    // 最多函数套64层
    CallFrame frames[FRAMES_MAX];
    int frameCount;
    // 虚拟机栈
    Value stack[STACK_MAX];
    // 指向栈顶元素的下一个位置
    Value *stackTop;
    // 全局变量表
    Table globals;
    // 字符串驻留集合
    // 用于存储所有运行时创建的字符串(去重)
    Table strings;
    // 所有的upvalue
    ObjUpvalue *openUpvalues;
    // 已分配内存的字节数
    size_t bytesAllocated;
    // 触发下次gc的字节阈值
    size_t nextGC;
    // lox对象链表
    Obj *objects;
    // 灰色对象列表 存储 Obj*
    int grayCount;
    int grayCapacity;
    Obj **grayStack;
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

void push(Value value);

Value pop();

#endif //CLOX_VM_H
