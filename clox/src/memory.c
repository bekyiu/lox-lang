#include "../header/memory.h"
#include "vm.h"

#ifdef DEBUG_LOG_GC

#include <stdio.h>
#include "debug.h"
#include "compiler.h"

#endif

#define GC_HEAP_GROW_FACTOR 2

void *reallocate(void *pointer, size_t oldSize, size_t newSize) {
    vm.bytesAllocated += newSize - oldSize;
    // 在要申请内存的时候 触发一次gc
    if (newSize > oldSize) {
#ifdef DEBUG_STRESS_GC
        collectGarbage();
#endif
        if (vm.bytesAllocated > vm.nextGC) {
            collectGarbage();
        }
    }

    if (newSize == 0) {
        free(pointer);
        return NULL;
    }

    void *result = realloc(pointer, newSize);
    if (result == NULL) {
        exit(1);
    }
    return result;
}

void markObject(Obj *object) {
    if (object == NULL) return;
    // 当对象出现循环引用的时候, 这样可以保证不会因为持续将同一批对象添加到灰色堆栈而陷入无限循环
    if (object->isMarked) return;
#ifdef DEBUG_LOG_GC
    printf("%p mark ", (void *) object);
    printValue(OBJ_VAL(object));
    printf("\n");
#endif
    object->isMarked = true;
    // 染色 灰色
    if (vm.grayCapacity < vm.grayCount + 1) {
        vm.grayCapacity = GROW_CAPACITY(vm.grayCapacity);
        // 不希望再gc时再出发gc, 所以用了标准库的申请内存的函数
        vm.grayStack = (Obj **) realloc(vm.grayStack, sizeof(Obj *) * vm.grayCapacity);
        if (vm.grayStack == NULL) exit(1);
    }
    vm.grayStack[vm.grayCount++] = object;
}

void markValue(Value value) {
    if (IS_OBJ(value)) markObject(AS_OBJ(value));
}

static void markArray(ValueArray *array) {
    for (int i = 0; i < array->count; i++) {
        markValue(array->values[i]);
    }
}

// 黑色对象是isMarked字段被设置且不再位于灰色栈中的任何对象
static void blackenObject(Obj *object) {
#ifdef DEBUG_LOG_GC
    printf("%p blacken ", (void *) object);
    printValue(OBJ_VAL(object));
    printf("\n");
#endif
    switch (object->type) {
        case OBJ_CLASS: {
            ObjClass *klass = (ObjClass *) object;
            markObject((Obj *) klass->name);
            markTable(&klass->methods);
            break;
        }
        case OBJ_CLOSURE: {
            ObjClosure *closure = (ObjClosure *) object;
            markObject((Obj *) closure->function);
            for (int i = 0; i < closure->upvalueCount; i++) {
                markObject((Obj *) closure->upvalues[i]);
            }
            break;
        }
        case OBJ_FUNCTION: {
            ObjFunction *function = (ObjFunction *) object;
            markObject((Obj *) function->name);
            markArray(&function->chunk.constants);
            break;
        }
        case OBJ_INSTANCE: {
            ObjInstance *instance = (ObjInstance *) object;
            markObject((Obj *) instance->klass);
            markTable(&instance->fields);
            break;
        }
        case OBJ_UPVALUE:
            markValue(((ObjUpvalue *) object)->closed);
            break;
        case OBJ_NATIVE:
        case OBJ_STRING:
            break;
    }
}

static void freeObject(Obj *object) {
#ifdef DEBUG_LOG_GC
    printf("\033[32m%p free type %d\033[0m\n", (void *) object, object->type);
#endif
    switch (object->type) {
        case OBJ_CLASS: {
            ObjClass *klass = (ObjClass *) object;
            freeTable(&klass->methods);
            FREE(ObjClass, object);
            break;
        }
        case OBJ_CLOSURE: {
            ObjClosure *closure = (ObjClosure *) object;
            FREE_ARRAY(ObjUpvalue*, closure->upvalues, closure->upvalueCount);
            FREE(ObjClosure, object);
            break;
        }
        case OBJ_FUNCTION: {
            ObjFunction *function = (ObjFunction *) object;
            freeChunk(&function->chunk);
            FREE(ObjFunction, object);
            break;
        }
        case OBJ_INSTANCE: {
            ObjInstance *instance = (ObjInstance *) object;
            freeTable(&instance->fields);
            FREE(ObjInstance, object);
            break;
        }
        case OBJ_NATIVE: {
            FREE(ObjNative, object);
            break;
        }
        case OBJ_STRING: {
            ObjString *str = (ObjString *) object;
            FREE_ARRAY(char, str->chars, str->length + 1);
            FREE(ObjString, object);
            break;
        }
        case OBJ_UPVALUE: {
            FREE(ObjUpvalue, object);
            break;
        }
    }
}

// 标记gc roots, 就是vm可以直接访问的对象
static void markRoots() {
    // 堆栈上的局部变量进行标记
    for (Value *slot = vm.stack; slot < vm.stackTop; slot++) {
        markValue(*slot);
    }
    // 标记闭包
    for (int i = 0; i < vm.frameCount; i++) {
        markObject((Obj *) vm.frames[i].closure);
    }
    // 标记upvalue
    for (ObjUpvalue *upvalue = vm.openUpvalues; upvalue != NULL; upvalue = upvalue->next) {
        markObject((Obj *) upvalue);
    }
    // 标记全局变量
    markTable(&vm.globals);
    // 编译期也可能会触发gc
    markCompilerRoots();
}

// 遍历灰色对象的引用, 把引用的对象变成灰色, 然后把自己变成黑色
static void traceReferences() {
    while (vm.grayCount > 0) {
        Obj *object = vm.grayStack[--vm.grayCount];
        blackenObject(object);
    }
}

static void sweep() {
    Obj *previous = NULL;
    Obj *object = vm.objects;
    while (object != NULL) {
        if (object->isMarked) {
            // 清除标记 为下轮gc做准备
            object->isMarked = false;
            previous = object;
            object = object->next;
        } else {
            Obj *unreached = object;
            object = object->next;
            if (previous != NULL) {
                previous->next = object;
            } else {
                vm.objects = object;
            }

            freeObject(unreached);
        }
    }
}

void collectGarbage() {
#ifdef DEBUG_LOG_GC
    printf("-- gc begin\n");
    size_t before = vm.bytesAllocated;
#endif

    markRoots();
    traceReferences();
    // 我们故意不将虚拟机的字符串表作为根的来源。如果我们这样做，就不会有字符串被回收 (因为我们的字符串是去过重的, 在内存里只有一份)
    // 同时，如果我们真的让GC释放字符串，那么VM的字符串表就会留下指向已释放内存的悬空指针, 这会更糟糕
    // 所以在染色完成后, 我们需要清除字符串表中的悬空指针
    // 对于这种被字符串表引用这的对象, 却仍可以被释放; 当释放后, 悬垂引用也被自动修正, 我们叫这种引用为weak reference
    tableRemoveWhite(&vm.strings);

    // 此时灰色栈是空的, 堆中的对象不是黑色就是白色
    // 而可达的对象一定是标记过的, 所以我们只要清楚没标记过的对象即可
    sweep();

    vm.nextGC = vm.bytesAllocated * GC_HEAP_GROW_FACTOR;
#ifdef DEBUG_LOG_GC
    printf("-- gc end\n");
    printf("   \033[31mcollected %zu bytes (from %zu to %zu) next at %zu\033[0m\n",
           before - vm.bytesAllocated, before, vm.bytesAllocated, vm.nextGC);
#endif
}

void freeObjects() {
    Obj *object = vm.objects;
    while (object != NULL) {
        Obj *next = object->next;
        freeObject(object);
        object = next;
    }
    free(vm.grayStack);
}