#include "chunk.h"
#include "debug.h"
#include "vm.h"

int main() {
    initVM();
    Chunk chunk;
    initChunk(&chunk);

    int constant = addConstant(&chunk, 99.2);
    writeChunk(&chunk, OP_CONSTANT, 12333);
    writeChunk(&chunk, constant, 12333);
    writeChunk(&chunk, OP_RETURN, 123334);

    disassembleChunk(&chunk, "test haha");
    interpret(&chunk);
    freeChunk(&chunk);
    freeVM();
    return 0;
}
