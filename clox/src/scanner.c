//
// Created by bekyiu on 2023/2/26.
//

#include "common.h"
#include "scanner.h"

typedef struct {
    // 正在被扫描的词素的起点
    const char *start;
    // 当前正在查看的字符
    const char *current;
    int line;
} Scanner;

Scanner scanner;

void initScanner(const char *source) {
    scanner.start = source;
    scanner.current = source;
    scanner.line = 1;
}

static bool isAtEnd() {
    return *(scanner.current) == '\0';
}

static Token makeToken(TokenType type) {
    Token token;
    token.type = type;
    token.start = scanner.start;
    token.length = (int) (scanner.current - scanner.start);
    token.line = scanner.line;

    return token;
}

static Token errorToken(const char *msg) {
    Token token;
    token.type = TOKEN_ERROR;
    token.start = msg;
    token.length = (int) strlen(msg);
    token.line = scanner.line;

    return token;
}

Token scanToken() {
    scanner.start = scanner.current;
    if (isAtEnd()) {
        return makeToken(TOKEN_EOF);
    }

    return errorToken("unexpected character");
}