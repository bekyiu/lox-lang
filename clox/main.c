#include "chunk.h"
#include "debug.h"
#include "vm.h"

int main() {
    initVM();
    Chunk chunk;
    initChunk(&chunk);

    int con1 = addConstant(&chunk, 1.2);
    writeChunk(&chunk, OP_CONSTANT, 12333);
    writeChunk(&chunk, con1, 12333);

    int con2 = addConstant(&chunk, 3.4);
    writeChunk(&chunk, OP_CONSTANT, 12333);
    writeChunk(&chunk, con2, 12333);


    // -(1.2 + 3.4) / 5.6)
    writeChunk(&chunk, OP_ADD, 12334);

    int con3 = addConstant(&chunk, 5.6);
    writeChunk(&chunk, OP_CONSTANT, 12333);
    writeChunk(&chunk, con3, 12333);

    writeChunk(&chunk, OP_DIVIDE, 12334);
    writeChunk(&chunk, OP_NEGATE, 12334);

    writeChunk(&chunk, OP_RETURN, 123334);

//    disassembleChunk(&chunk, "test haha");
    interpret(&chunk);
    freeChunk(&chunk);
    freeVM();
    return 0;
}
