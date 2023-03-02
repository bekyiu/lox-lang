//
// Created by bekyiu on 2023/3/1.
//

#include "object.h"
#include "../header/memory.h"

// 第一个type是
#define ALLOCATE_OBJ(type, objType) \
    (type*)allocateObject(sizeof(type), objType)

// 创建指定类型的Obj对象
// 返回的是父类
static Obj *allocateObject(size_t size, ObjType type) {
    Obj *object = (Obj *) reallocate(NULL, 0, size);
    object->type = type;
    return object;
}


static ObjString *allocateString(char *str, int length) {
    ObjString *ret = ALLOCATE_OBJ(ObjString, OBJ_STRING);
    ret->length = length;
    ret->chars = str;
    return ret;
}

ObjString *takeString(char *chars, int length) {
    return allocateString(chars, length);
}

ObjString *copyString(const char *chars, int length) {
    char *str = ALLOCATE(char, length + 1);
    memcpy(str, chars, length);
    str[length] = '\0';
    return allocateString(str, length);
}

void printObject(Value value) {
    switch (OBJ_TYPE(value)) {
        case OBJ_STRING:
            printf("%s", AS_CSTRING(value));
            break;
    }
}