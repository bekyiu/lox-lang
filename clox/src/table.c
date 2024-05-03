//
// Created by bekyiu on 2023/3/5.
//

#include "table.h"
#include "../header/memory.h"
#include "object.h"
#include "value.h"

#define TABLE_MAX_LOAD 0.75

void initTable(Table *table) {
    table->count = 0;
    table->capacity = 0;
    table->entries = NULL;
}

void freeTable(Table *table) {
    FREE_ARRAY(Entry, table->entries, table->capacity);
    initTable(table);
}

static Entry *findEntry(Entry *entries, int capacity, ObjString *key) {
    uint32_t index = key->hash % capacity;
    Entry *tombstone = NULL;
    // 不能把墓碑当做空entry 否则这里可能会死循环
    for (;;) {
        Entry *entry = &entries[index];
        if (entry->key == NULL) {
            if (IS_NIL(entry->value)) {
                // Empty entry.
                return tombstone != NULL ? tombstone : entry;
            } else {
                // We found a tombstone.
                if (tombstone == NULL) {
                    tombstone = entry;
                }
            }
        } else if (entry->key == key) {
            // We found the key.
            return entry;
        }

        index = (index + 1) % capacity;
    }
}

static void adjustCapacity(Table *table, int capacity) {
    // 分配新数组
    Entry *entries = ALLOCATE(Entry, capacity);
    for (int i = 0; i < capacity; i++) {
        entries[i].key = NULL;
        entries[i].value = NIL_VAL;
    }

    table->count = 0;
    // 重新计算索引
    for (int i = 0; i < table->capacity; i++) {
        Entry *entry = &table->entries[i];
        if (entry->key == NULL) {
            continue;
        }

        Entry *dest = findEntry(entries, capacity, entry->key);
        dest->key = entry->key;
        dest->value = entry->value;
        table->count++;
    }
    // 释放旧数组
    FREE_ARRAY(Entry, table->entries, table->capacity);

    table->entries = entries;
    table->capacity = capacity;
}

bool tableSet(Table *table, ObjString *key, Value value) {
    // 扩容
    if (table->count + 1 > table->capacity * TABLE_MAX_LOAD) {
        int capacity = GROW_CAPACITY(table->capacity);
        adjustCapacity(table, capacity);
    }
    // 找到一个可用的entry
    Entry *entry = findEntry(table->entries, table->capacity, key);
    bool isNewKey = entry->key == NULL;
    if (isNewKey && IS_NIL(entry->value)) {
        table->count++;
    }

    entry->key = key;
    entry->value = value;
    return isNewKey;
}


void tableAddAll(Table *from, Table *to) {
    for (int i = 0; i < from->capacity; i++) {
        Entry *entry = &from->entries[i];
        if (entry->key != NULL) {
            tableSet(to, entry->key, entry->value);
        }
    }
}

bool tableGet(Table *table, ObjString *key, Value *value) {
    if (table->count == 0) {
        return false;
    }

    Entry *entry = findEntry(table->entries, table->capacity, key);
    if (entry->key == NULL) {
        return false;
    }

    *value = entry->value;
    return true;
}

bool tableDelete(Table *table, ObjString *key) {
    if (table->count == 0) {
        return false;
    }

    // Find the entry.
    Entry *entry = findEntry(table->entries, table->capacity, key);
    if (entry->key == NULL) {
        return false;
    }

    // Place a tombstone in the entry.
    entry->key = NULL;
    entry->value = BOOL_VAL(true);
    // 注意 这里没有对count减一, 我们需要把墓碑也当做占用位置的一个entry
    return true;
}

ObjString *tableFindString(Table *table, const char *chars, int length, uint32_t hash) {
    if (table->count == 0) {
        return NULL;
    }

    uint32_t index = hash % table->capacity;
    for (;;) {
        Entry *entry = &table->entries[index];
        if (entry->key == NULL) {
            // Stop if we find an empty non-tombstone entry.
            // 遇到墓碑不能停, 可能要查找的字符串在墓碑后面
            if (IS_NIL(entry->value)) {
                return NULL;
            }
        } else if (entry->key->length == length &&
                   entry->key->hash == hash &&
                   memcmp(entry->key->chars, chars, length) == 0) {
            // We found it.
            return entry->key;
        }

        index = (index + 1) % table->capacity;
    }
}

void tableRemoveWhite(Table *table) {
    for (int i = 0; i < table->capacity; i++) {
        Entry *entry = &table->entries[i];
        if (entry->key != NULL && !entry->key->obj.isMarked) {
            tableDelete(table, entry->key);
        }
    }
}

void markTable(Table *table) {
    for (int i = 0; i < table->capacity; i++) {
        Entry *entry = &table->entries[i];
        markObject((Obj *) entry->key);
        markValue(entry->value);
    }
}