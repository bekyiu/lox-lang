#include <stdio.h>

#include "../header/debug.h"

void disassembleChunk(Chunk *chunk, const char *name) {
    log("== %s ==\n", name);
    log("%8s %8s %-16s %8s %s\n", "offset", "line", "opcode", "conIdx", "conVal");

    for (int offset = 0; offset < chunk->count;) {
        offset = disassembleInstruction(chunk, offset);
    }
}

// opcode
static int simpleInstruction(const char *name, int offset) {
    printf("%s\n", name);
    return offset + 1;
}

// opcode operand
static int constantInstruction(const char *name, Chunk *chunk, int offset) {
    uint8_t constantIdx = chunk->code[offset + 1];
    printf("%-16s %8d '", name, constantIdx);
    printValue(chunk->constants.values[constantIdx]);
    printf("'\n");
    return offset + 2;
}

int disassembleInstruction(Chunk *chunk, int offset) {
    printf("%08d ", offset);
    if (offset > 0 && chunk->lines[offset] == chunk->lines[offset - 1]) {
        printf("       | ");
    } else {
        printf("%8d ", chunk->lines[offset]);
    }
    uint8_t instruction = chunk->code[offset];
    switch (instruction) {
        case OP_CONSTANT:
            return constantInstruction("OP_CONSTANT", chunk, offset);
        case OP_RETURN:
            return simpleInstruction("OP_RETURN", offset);
        default:
            printf("Unknown opcode %d\n", instruction);
            return offset + 1;
    }
}

