//
// Created by bekyiu on 2023/3/1.
//

#include "object.h"
#include "vm.h"
#include "../header/memory.h"
#include "table.h"

// 第一个type是
#define ALLOCATE_OBJ(type, objType) \
    (type*)allocateObject(sizeof(type), objType)

// 创建指定类型的Obj对象
// 返回的是父类
static Obj *allocateObject(size_t size, ObjType type) {
    Obj *object = (Obj *) reallocate(NULL, 0, size);
    object->type = type;
    object->next = vm.objects;
    vm.objects = object;
    return object;
}


static ObjString *allocateString(char *str, int length, uint32_t hash) {
    ObjString *ret = ALLOCATE_OBJ(ObjString, OBJ_STRING);
    ret->length = length;
    ret->chars = str;
    ret->hash = hash;
    tableSet(&vm.strings, ret, NIL_VAL);
    return ret;
}

// FNV-1a hash算法
static uint32_t hashString(const char *key, int length) {
    uint32_t hash = 2166136261u;
    for (int i = 0; i < length; i++) {
        hash ^= (uint8_t) key[i];
        hash *= 16777619;
    }
    return hash;
}

ObjString *takeString(char *chars, int length) {
    uint32_t hash = hashString(chars, length);
    ObjString *interned = tableFindString(&vm.strings, chars, length, hash);
    if (interned != NULL) {
        FREE_ARRAY(char, chars, length + 1);
        return interned;
    }
    return allocateString(chars, length, hash);
}

ObjString *copyString(const char *chars, int length) {
    uint32_t hash = hashString(chars, length);

    // 先查字符串驻留表
    ObjString *interned = tableFindString(&vm.strings, chars, length, hash);
    if (interned != NULL) {
        return interned;
    }

    char *str = ALLOCATE(char, length + 1);
    memcpy(str, chars, length);
    str[length] = '\0';
    return allocateString(str, length, hash);
}

void printObject(Value value) {
    switch (OBJ_TYPE(value)) {
        case OBJ_STRING:
            printf("%s", AS_CSTRING(value));
            break;
    }
}