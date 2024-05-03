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
    object->isMarked = false;
    object->next = vm.objects;
    vm.objects = object;
#ifdef DEBUG_LOG_GC
    printf("%p allocate %zu for %d\n", (void *) object, size, type);
#endif
    return object;
}


static ObjString *allocateString(char *str, int length, uint32_t hash) {
    ObjString *ret = ALLOCATE_OBJ(ObjString, OBJ_STRING);
    ret->length = length;
    ret->chars = str;
    ret->hash = hash;
    // 这个时候ret才创建 还未被标记
    // 在tableSet中如果的hash表扩容, 就会回收掉这个字符串, 这显然是不对的, 因为我们后续还需要使用这个字符串
    // 所以这里先把他压入栈中, 这样就是一个gc root了
    push(OBJ_VAL(ret));
    tableSet(&vm.strings, ret, NIL_VAL);
    pop();
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


static void printFunction(ObjFunction *function) {
    if (function->name == NULL) {
        printf("<script>");
        return;
    }
    printf("<fn %s>", function->name->chars);
}


void printObject(Value value) {
    switch (OBJ_TYPE(value)) {
        case OBJ_CLOSURE:
            printFunction(AS_CLOSURE(value)->function);
            break;
        case OBJ_FUNCTION:
            printFunction(AS_FUNCTION(value));
            break;
        case OBJ_NATIVE:
            printf("<native fn>");
            break;
        case OBJ_STRING:
            printf("%s", AS_CSTRING(value));
            break;
        case OBJ_UPVALUE:
            printf("upvalue");
            break;
    }
}

ObjFunction *newFunction() {
    ObjFunction *function = ALLOCATE_OBJ(ObjFunction, OBJ_FUNCTION);
    function->arity = 0;
    function->upvalueCount = 0;
    function->name = NULL;
    initChunk(&function->chunk);
    return function;
}

ObjNative *newNative(NativeFn function) {
    ObjNative *native = ALLOCATE_OBJ(ObjNative, OBJ_NATIVE);
    native->function = function;
    return native;
}

ObjClosure *newClosure(ObjFunction *function) {
    ObjUpvalue **upvalues = ALLOCATE(ObjUpvalue*, function->upvalueCount);
    for (int i = 0; i < function->upvalueCount; i++) {
        upvalues[i] = NULL;
    }

    ObjClosure *closure = ALLOCATE_OBJ(ObjClosure, OBJ_CLOSURE);
    closure->function = function;
    closure->upvalues = upvalues;
    closure->upvalueCount = function->upvalueCount;
    return closure;
}

ObjUpvalue *newUpvalue(Value *slot) {
    ObjUpvalue *upvalue = ALLOCATE_OBJ(ObjUpvalue, OBJ_UPVALUE);
    upvalue->closed = NIL_VAL;
    upvalue->location = slot;
    upvalue->next = NULL;
    return upvalue;
}