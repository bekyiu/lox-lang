//
// Created by bekyiu on 2023/2/26.
//

#ifndef CLOX_COMPILER_H
#define CLOX_COMPILER_H

#include "chunk.h"

bool compile(const char *source, Chunk *chunk);

#endif //CLOX_COMPILER_H
