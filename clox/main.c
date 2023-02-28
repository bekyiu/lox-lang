#include "chunk.h"
#include "debug.h"
#include "vm.h"
#include "common.h"

static void repl() {
    char line[1024] = {'\0'};
    while (true) {
        printf("> ");

        // 从 stdin 读取一行数据到line中
        // 当读取 (n-1) 个字符时，或者读取到换行符时，或者到达文件末尾时，它会停止
        // 如果成功，该函数返回相同的 str 参数。如果到达文件末尾或者没有读取到任何字符，str 的内容保持不变，并返回一个空指针。
        // 如果发生错误，返回一个空指针
        if (!fgets(line, sizeof(line), stdin)) {
            printf("\n");
            break;
        }

        interpret(line);
    }
}

static char *readFile(const char *path) {
    // 读写打开一个二进制文件，允许读数据
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        fprintf(stderr, "can not open file: %s\n", path);
        exit(74);
    }
    // 把文件指针移动到末尾
    fseek(file, 0L, SEEK_END);
    // 从文件开始到当前位置一共有多少个字节 这里就是计算文件大小
    size_t fileSize = ftell(file);
    // 将文件指针移到开头
    rewind(file);

    char *buffer = (char *) malloc(fileSize + 1);
    if (buffer == NULL) {
        fprintf(stderr, "not enough memory to read file: %s\n", path);
        exit(74);
    }
    // 从file里读数据 读到buffer里
    // 一共读fileSize个单位, 每个单位 sizeof(char) 个字节
    // 返回成功读取的单位个数
    size_t bytesRead = fread(buffer, sizeof(char), fileSize, file);
    if (bytesRead < fileSize) {
        fprintf(stderr, "can not read file: %s\n", path);
        exit(74);
    }
    buffer[bytesRead] = '\0';

    fclose(file);
    return buffer;
}

static void runFile(const char *path) {
    char *source = readFile(path);
    InterpretResult result = interpret(source);
    free(source);

    if (result == INTERPRET_COMPILE_ERROR) {
        exit(65);
    }
    if (result == INTERPRET_RUNTIME_ERROR) {
        exit(70);
    }
}

int main(int argc, const char *argv[]) {
    initVM();

    if (argc == 1) {
        repl();
    } else if (argc == 2) {
        runFile(argv[1]);
    } else {
        fprintf(stderr, "usage: clox [path]\n");
        exit(64);
    }

    freeVM();
    return 0;
}
