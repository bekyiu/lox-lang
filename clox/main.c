#include <stdio.h>
#include <stdint.h>
#include "header/chunk.h"
#include "header/debug.h"

int main() {
    Chunk chunk;
    initChunk(&chunk);

    int constant = addConstant(&chunk, 1.2);
    writeChunk(&chunk, OP_CONSTANT, 12333);
    writeChunk(&chunk, constant, 12333);
    writeChunk(&chunk, OP_RETURN, 123334);

    disassembleChunk(&chunk, "test haha");
    freeChunk(&chunk);
    return 0;
}
