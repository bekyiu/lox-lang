//
// Created by bekyiu on 2023/3/1.
//

#ifndef CLOX_OBJECT_H
#define CLOX_OBJECT_H

#include "common.h"
#include "value.h"
#include "chunk.h"

// 在堆上分配内存的lox value类型
typedef enum {
    OBJ_CLOSURE,
    OBJ_FUNCTION,
    OBJ_NATIVE,
    OBJ_STRING,
    OBJ_UPVALUE,
} ObjType;

// 所有lox对象的父类
struct Obj {
    ObjType type;
    // 用于记录所有分配的lox对象 因为需要被释放
    struct Obj *next;
};

typedef struct {
    Obj obj;
    int arity;
    // 当前这个函数已经捕获了多少外围的局部变量
    int upvalueCount;
    Chunk chunk;
    ObjString *name;
} ObjFunction;

// upvalue在运行时的表示
typedef struct ObjUpvalue {
    Obj obj;
    // 被捕获的值
    Value *location;
    // 保存栈中被销毁的局部变量
    Value closed;
    struct ObjUpvalue* next;
} ObjUpvalue;

typedef struct {
    Obj obj;
    ObjFunction *function;
    // 指向动态分配的 ObjUpvalue*数组
    ObjUpvalue **upvalues;
    int upvalueCount;
} ObjClosure;

struct ObjString {
    Obj obj;
    int length;
    char *chars;
    uint32_t hash;
};

// 本地函数接口
// 入参是参数个数和指向栈中第一个参数的指针
typedef Value (*NativeFn)(int argCount, Value *args);

typedef struct {
    Obj obj;
    NativeFn function;
} ObjNative;

#define OBJ_TYPE(value)        (AS_OBJ(value)->type)
#define IS_CLOSURE(value)      isObjType(value, OBJ_CLOSURE)
#define IS_FUNCTION(value)     isObjType(value, OBJ_FUNCTION)
#define IS_STRING(value)       isObjType(value, OBJ_STRING)
#define IS_NATIVE(value)       isObjType(value, OBJ_NATIVE)

#define AS_CLOSURE(value)      ((ObjClosure*)AS_OBJ(value))
#define AS_FUNCTION(value)     ((ObjFunction*)AS_OBJ(value))
#define AS_STRING(value)       ((ObjString*)AS_OBJ(value))
#define AS_CSTRING(value)      (((ObjString*)AS_OBJ(value))->chars)
#define AS_NATIVE(value) \
    (((ObjNative*)AS_OBJ(value))->function)

static inline bool isObjType(Value value, ObjType type) {
    return IS_OBJ(value) && AS_OBJ(value)->type == type;
}

ObjNative *newNative(NativeFn function);

ObjFunction *newFunction();

ObjClosure *newClosure(ObjFunction *function);

ObjString *takeString(char *chars, int length);

ObjString *copyString(const char *chars, int length);

ObjUpvalue *newUpvalue(Value *slot);

void printObject(Value value);

#endif //CLOX_OBJECT_H
