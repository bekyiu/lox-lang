//
// Created by bekyiu on 2023/2/24.
//
#include "vm.h"
#include "common.h"
#include "value.h"

VM vm;

void initVM() {

}

void freeVM() {

}

static InterpretResult run() {
// 先取到ip指向的值 作为返回值, 在把ip++
#define READ_BYTE() (*(vm.ip++))
#define READ_CONSTANT() (vm.chunk->constants.values[READ_BYTE()])

    while (true) {
        uint8_t opcode;
        switch (opcode = READ_BYTE()) {
            case OP_CONSTANT: {
                Value constant = READ_CONSTANT();
                printValue(constant);
                printf("\n");
                break;
            }

            case OP_RETURN: {
                return INTERPRET_OK;
            }
        }
    }

#undef READ_CONSTANT
#undef READ_BYTE
}

InterpretResult interpret(Chunk *chunk) {
    vm.chunk = chunk;
    vm.ip = chunk->code;
    return run();
}