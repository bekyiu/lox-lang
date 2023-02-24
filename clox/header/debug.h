#ifndef CLOX_DEBUG_H
#define CLOX_DEBUG_H

#include "chunk.h"

#define log(...) printf(__VA_ARGS__)

void disassembleChunk(Chunk *chunk, const char *name);

int disassembleInstruction(Chunk *chunk, int offset);

#endif //CLOX_DEBUG_H
