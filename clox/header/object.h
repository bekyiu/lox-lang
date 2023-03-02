//
// Created by bekyiu on 2023/3/1.
//

#ifndef CLOX_OBJECT_H
#define CLOX_OBJECT_H

#include "common.h"
#include "value.h"

// 在堆上分配内存的lox value类型
typedef enum {
    OBJ_STRING,
} ObjType;

// 所有lox对象的父类
struct Obj {
    ObjType type;
};

struct ObjString {
    Obj obj;
    int length;
    char *chars;
};

#define OBJ_TYPE(value)        (AS_OBJ(value)->type)
#define IS_STRING(value)       isObjType(value, OBJ_STRING)

#define AS_STRING(value)       ((ObjString*)AS_OBJ(value))
#define AS_CSTRING(value)      (((ObjString*)AS_OBJ(value))->chars)

static inline bool isObjType(Value value, ObjType type) {
    return IS_OBJ(value) && AS_OBJ(value)->type == type;
}

ObjString *takeString(char *chars, int length);

ObjString *copyString(const char *chars, int length);

void printObject(Value value);

#endif //CLOX_OBJECT_H
