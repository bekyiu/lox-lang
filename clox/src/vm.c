//
// Created by bekyiu on 2023/2/24.
//
#include "vm.h"
#include "common.h"
#include "value.h"
#include "debug.h"
#include "compiler.h"
#include "../header/memory.h"
#include <stdarg.h>

VM vm;

static void resetStack() {
    vm.stackTop = vm.stack;
    vm.frameCount = 0;
}

void push(Value value) {
    *(vm.stackTop) = value;
    vm.stackTop++;
}

Value pop() {
    vm.stackTop--;
    return *(vm.stackTop);
}

static Value peek(int distance) {
    return *(vm.stackTop - 1 - distance);
}

static void runtimeError(const char *format, ...) {
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
    fputs("\n", stderr);

    // 打印堆栈异常
    for (int i = vm.frameCount - 1; i >= 0; i--) {
        CallFrame *frame = &vm.frames[i];
        ObjFunction *function = frame->function;
        size_t instruction = frame->ip - function->chunk.code - 1;
        fprintf(stderr, "[line %d] in ", function->chunk.lines[instruction]);
        if (function->name == NULL) {
            fprintf(stderr, "script\n");
        } else {
            fprintf(stderr, "%s()\n", function->name->chars);
        }
    }
    resetStack();
}


static bool call(ObjFunction *function, int argCount) {
    if (argCount != function->arity) {
        runtimeError("Expected %d arguments but got %d.",
                     function->arity, argCount);
        return false;
    }

    if (vm.frameCount == FRAMES_MAX) {
        runtimeError("Stack overflow.");
        return false;
    }

    CallFrame *frame = &vm.frames[vm.frameCount++];
    frame->function = function;
    frame->ip = function->chunk.code;
    frame->slots = vm.stackTop - argCount - 1;
    return true;
}


static bool callValue(Value callee, int argCount) {
    if (IS_OBJ(callee)) {
        switch (OBJ_TYPE(callee)) {
            case OBJ_FUNCTION:
                return call(AS_FUNCTION(callee), argCount);
            default:
                break; // Non-callable object type.
        }
    }
    runtimeError("Can only call functions and classes.");
    return false;
}

// nil和false是假的，其它的值都表现为true
static bool isFalsey(Value value) {
    return IS_NIL(value) || (IS_BOOL(value) && !AS_BOOL(value));
}

// 字符串拼接
static void concatenate() {
    // gc会free这些被pop的字符串
    ObjString *b = AS_STRING(pop());
    ObjString *a = AS_STRING(pop());

    int len = a->length + b->length;
    char *str = ALLOCATE(char, len + 1);
    memcpy(str, a->chars, a->length);
    memcpy(str + a->length, b->chars, b->length);
    str[len] = '\0';

    ObjString *ret = takeString(str, len);
    push(OBJ_VAL(ret));
}

void initVM() {
    resetStack();
    vm.objects = NULL;
    initTable(&vm.globals);
    initTable(&vm.strings);
}

void freeVM() {
    freeTable(&vm.globals);
    freeTable(&vm.strings);
    freeObjects();
}

static InterpretResult run() {
    CallFrame *frame = &vm.frames[vm.frameCount - 1];

// 先取到ip指向的值 作为返回值, 在把ip++
#define READ_BYTE() (*(frame->ip++))
#define READ_CONSTANT() (frame->function->chunk.constants.values[READ_BYTE()])
#define READ_STRING() AS_STRING(READ_CONSTANT())
#define READ_SHORT() \
    (frame->ip += 2, (uint16_t)((frame->ip[-2] << 8) | frame->ip[-1]))
#define BINARY_OP(valueType, op) \
do { \
    if(!IS_NUMBER(peek(0)) || !IS_NUMBER(peek(1))) { \
        runtimeError("Operands must be numbers."); \
        return INTERPRET_RUNTIME_ERROR; \
    } \
    double b = AS_NUMBER(pop()); \
    double a = AS_NUMBER(pop()); \
    push(valueType(a op b)); \
} while(0)

    while (true) {
#ifdef DEBUG_TRACE_EXECUTION
        printf("stack: ");
        for (Value *slot = vm.stack; slot < vm.stackTop; slot++) {
            printf("[ ");
            printValue(*slot);
            printf(" ]");
        }
        printf("\n");
        disassembleInstruction(&frame->function->chunk, (int) (frame->ip - frame->function->chunk.code));
#endif
        uint8_t opcode;
        switch (opcode = READ_BYTE()) {
            case OP_CONSTANT: {
                Value constant = READ_CONSTANT();
                push(constant);
                break;
            }
            case OP_NIL: {
                push(NIL_VAL);
                break;
            }
            case OP_TRUE: {
                push(BOOL_VAL(true));
                break;
            }
            case OP_FALSE: {
                push(BOOL_VAL(false));
                break;
            }
            case OP_POP: {
                pop();
                break;
            }
            case OP_GET_LOCAL: {
                // 局部变量在栈中的索引
                uint8_t slot = READ_BYTE();
                push(frame->slots[slot]);
                break;
            }
            case OP_SET_LOCAL: {
                uint8_t slot = READ_BYTE();
                // 赋值是表达式 有返回值 所以不要pop
                frame->slots[slot] = peek(0);
                break;
            }
            case OP_GET_GLOBAL: {
                ObjString *name = READ_STRING();
                Value value;
                if (!tableGet(&vm.globals, name, &value)) {
                    runtimeError("Undefined variable '%s'.", name->chars);
                    return INTERPRET_RUNTIME_ERROR;
                }
                push(value);
                break;
            }
            case OP_DEFINE_GLOBAL: {
                ObjString *name = READ_STRING();
                // 此时栈顶是表达式的结果
                // 先存在map里, 再pop
                // 因为存map的时候可能会触发gc
                tableSet(&vm.globals, name, peek(0));
                pop();
                break;
            }
            case OP_SET_GLOBAL: {
                ObjString *name = READ_STRING();
                if (tableSet(&vm.globals, name, peek(0))) {
                    // 如果 name不在全局变量表中 就不能对其进行赋值 (因为不能对一个不存在的变量进行赋值)
                    tableDelete(&vm.globals, name);
                    runtimeError("Undefined variable '%s'.", name->chars);
                    return INTERPRET_RUNTIME_ERROR;
                }
                break;
            }
            case OP_EQUAL: {
                Value b = pop();
                Value a = pop();
                push(BOOL_VAL(valuesEqual(a, b)));
                break;
            }
            case OP_GREATER: {
                BINARY_OP(BOOL_VAL, >);
                break;
            }
            case OP_LESS: {
                BINARY_OP(BOOL_VAL, <);
                break;
            }
            case OP_ADD: {
                Value b = peek(0);
                Value a = peek(0);
                if (IS_STRING(b) && IS_STRING(a)) {
                    concatenate();
                } else if (IS_NUMBER(b) && IS_NUMBER(a)) {
                    double vb = AS_NUMBER(pop());
                    double va = AS_NUMBER(pop());
                    push(NUMBER_VAL(va + vb));
                } else {
                    runtimeError("Operands must be two numbers or two strings.");
                    return INTERPRET_RUNTIME_ERROR;
                }
                break;
            }
            case OP_SUBTRACT: {
                BINARY_OP(NUMBER_VAL, -);
                break;
            }
            case OP_MULTIPLY: {
                BINARY_OP(NUMBER_VAL, *);
                break;
            }
            case OP_DIVIDE: {
                BINARY_OP(NUMBER_VAL, /);
                break;
            }
            case OP_NOT: {
                push(BOOL_VAL(isFalsey(pop())));
                break;
            }
            case OP_NEGATE: {
                if (!IS_NUMBER(peek(0))) {
                    runtimeError("Operand must be a number.");
                    return INTERPRET_RUNTIME_ERROR;
                }
                push(NUMBER_VAL(-AS_NUMBER(pop())));
                break;
            }
            case OP_PRINT: {
                printValue(pop());
                printf("\n");
                break;
            }
            case OP_JUMP: {
                uint16_t offset = READ_SHORT();
                frame->ip += offset;
                break;
            }
            case OP_JUMP_IF_FALSE: {
                uint16_t offset = READ_SHORT();
                // 并未弹出 是由pop指令弹出的
                if (isFalsey(peek(0))) {
                    frame->ip += offset;
                }
                break;
            }
            case OP_LOOP: {
                uint16_t offset = READ_SHORT();
                frame->ip -= offset;
                break;
            }
            case OP_CALL: {
                int argCount = READ_BYTE();
                if (!callValue(peek(argCount), argCount)) {
                    return INTERPRET_RUNTIME_ERROR;
                }
                // 切到新的函数执行
                frame = &vm.frames[vm.frameCount - 1];
                break;
            }
            case OP_RETURN: {
                // 拿到返回值
                Value result = pop();
                vm.frameCount--;
                // 顶层不能写return 但是又读到return指令 说明是endCompiler了 结束执行
                if (vm.frameCount == 0) {
                    pop();
                    return INTERPRET_OK;
                }
                // 回退栈指针
                vm.stackTop = frame->slots;
                // 压入返回值
                push(result);
                // 切到上个函数
                frame = &vm.frames[vm.frameCount - 1];
                break;
            }
        }
    }

#undef BINARY_OP
#undef READ_SHORT
#undef READ_STRING
#undef READ_CONSTANT
#undef READ_BYTE
}

InterpretResult interpret(const char *source) {
    ObjFunction *function = compile(source);
    if (function == NULL) {
        return INTERPRET_COMPILE_ERROR;
    }

    push(OBJ_VAL(function));
    call(function, 0);


    InterpretResult ret = run();
    return ret;
}