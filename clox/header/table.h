//
// Created by bekyiu on 2023/3/5.
//

#ifndef CLOX_TABLE_H
#define CLOX_TABLE_H

#include "value.h"
#include "common.h"

typedef struct {
    ObjString *key;
    Value value;
} Entry;

// 开放地址法的hash表
// 线性探测
typedef struct {
    int count;
    int capacity;
    Entry *entries;
} Table;

void initTable(Table *table);

void freeTable(Table *table);

bool tableSet(Table *table, ObjString *key, Value value);

// 浅拷贝
void tableAddAll(Table *from, Table *to);

// 找到返回true, 找不到返回false
bool tableGet(Table *table, ObjString *key, Value *value);

bool tableDelete(Table *table, ObjString *key);

ObjString *tableFindString(Table *table, const char *chars, int length, uint32_t hash);

void markTable(Table* table);

#endif //CLOX_TABLE_H
