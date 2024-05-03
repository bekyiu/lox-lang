//
// Created by bekyiu on 2023/2/26.
//

#include "debug.h"
#include "compiler.h"
#include "scanner.h"
#include "memory.h"
#include "common.h"

typedef enum {
    PREC_NONE,
    PREC_ASSIGNMENT,  // =
    PREC_OR,          // or
    PREC_AND,         // and
    PREC_EQUALITY,    // == !=
    PREC_COMPARISON,  // < > <= >=
    PREC_TERM,        // + -
    PREC_FACTOR,      // * /
    PREC_UNARY,       // ! -
    PREC_CALL,        // . ()
    PREC_PRIMARY
} Precedence;

typedef void (*ParseFn)(bool canAssign);

typedef struct {
    ParseFn prefix;
    ParseFn infix;
    Precedence precedence;
} ParseRule;

typedef struct {
    Token current;
    Token previous;
    bool hadError;
    bool panicMode;
} Parser;

typedef struct {
    // 局部变量名字
    Token name;
    // 作用域深度
    int depth;
    // 是否被任何闭包捕获
    bool isCaptured;
} Local;

typedef struct {
    // 捕获的是哪个局部变量槽
    uint8_t index;
    // true说明捕获的是外围函数的局部变量
    // false说明捕获的是外围函数的上值
    bool isLocal;
} Upvalue;

typedef enum {
    TYPE_FUNCTION,
    TYPE_SCRIPT
} FunctionType;

typedef struct {
    // 一共256个局部变量可用
    Local locals[UINT8_COUNT];
    // 有多少个数组槽在使用
    int localCount;
    // 当前函数捕获的 外层局部变量或者upvalue
    Upvalue upvalues[UINT8_COUNT];
    // 作用域深度 0就是全局变量
    int scopeDepth;
    // 最外层的代码也当做一个函数
    ObjFunction *function;
    FunctionType type;
    // 指向外围函数
    struct Compiler *enclosing;
} Compiler;

Parser parser;


Compiler *current = NULL;

static void grouping(bool canAssign);

static void unary(bool canAssign);

static void binary(bool canAssign);

static void number(bool canAssign);

static void literal(bool canAssign);

static void string(bool canAssign);

static void variable(bool canAssign);

static void and(bool canAssign);

static void or(bool canAssign);

static void call(bool canAssign);


static void statement();

static void declaration();

static void varDeclaration();

ParseRule rules[] = {
        [TOKEN_LEFT_PAREN]    = {grouping, call, PREC_CALL},
        [TOKEN_RIGHT_PAREN]   = {NULL, NULL, PREC_NONE},
        [TOKEN_LEFT_BRACE]    = {NULL, NULL, PREC_NONE},
        [TOKEN_RIGHT_BRACE]   = {NULL, NULL, PREC_NONE},
        [TOKEN_COMMA]         = {NULL, NULL, PREC_NONE},
        [TOKEN_DOT]           = {NULL, NULL, PREC_NONE},
        [TOKEN_MINUS]         = {unary, binary, PREC_TERM},
        [TOKEN_PLUS]          = {NULL, binary, PREC_TERM},
        [TOKEN_SEMICOLON]     = {NULL, NULL, PREC_NONE},
        [TOKEN_SLASH]         = {NULL, binary, PREC_FACTOR},
        [TOKEN_STAR]          = {NULL, binary, PREC_FACTOR},
        [TOKEN_BANG]          = {unary, NULL, PREC_NONE},
        [TOKEN_BANG_EQUAL]    = {NULL, binary, PREC_EQUALITY},
        [TOKEN_EQUAL]         = {NULL, NULL, PREC_NONE},
        [TOKEN_EQUAL_EQUAL]   = {NULL, binary, PREC_EQUALITY},
        [TOKEN_GREATER]       = {NULL, binary, PREC_COMPARISON},
        [TOKEN_GREATER_EQUAL] = {NULL, binary, PREC_COMPARISON},
        [TOKEN_LESS]          = {NULL, binary, PREC_COMPARISON},
        [TOKEN_LESS_EQUAL]    = {NULL, binary, PREC_COMPARISON},
        [TOKEN_IDENTIFIER]    = {variable, NULL, PREC_NONE},
        [TOKEN_STRING]        = {string, NULL, PREC_NONE},
        [TOKEN_NUMBER]        = {number, NULL, PREC_NONE},
        [TOKEN_AND]           = {NULL, and, PREC_AND},
        [TOKEN_CLASS]         = {NULL, NULL, PREC_NONE},
        [TOKEN_ELSE]          = {NULL, NULL, PREC_NONE},
        [TOKEN_FALSE]         = {literal, NULL, PREC_NONE},
        [TOKEN_FOR]           = {NULL, NULL, PREC_NONE},
        [TOKEN_FUN]           = {NULL, NULL, PREC_NONE},
        [TOKEN_IF]            = {NULL, NULL, PREC_NONE},
        [TOKEN_NIL]           = {literal, NULL, PREC_NONE},
        [TOKEN_OR]            = {NULL, or, PREC_OR},
        [TOKEN_PRINT]         = {NULL, NULL, PREC_NONE},
        [TOKEN_RETURN]        = {NULL, NULL, PREC_NONE},
        [TOKEN_SUPER]         = {NULL, NULL, PREC_NONE},
        [TOKEN_THIS]          = {NULL, NULL, PREC_NONE},
        [TOKEN_TRUE]          = {literal, NULL, PREC_NONE},
        [TOKEN_VAR]           = {NULL, NULL, PREC_NONE},
        [TOKEN_WHILE]         = {NULL, NULL, PREC_NONE},
        [TOKEN_ERROR]         = {NULL, NULL, PREC_NONE},
        [TOKEN_EOF]           = {NULL, NULL, PREC_NONE},
};

static ParseRule *getRule(TokenType type) {
    return &rules[type];
}

static Chunk *currentChunk() {
    return &current->function->chunk;
}

static void initCompiler(Compiler *compiler, FunctionType type) {
    // 指向上一层compiler
    compiler->enclosing = (struct Compiler *) current;
    compiler->type = type;
    compiler->localCount = 0;
    compiler->scopeDepth = 0;
    compiler->function = newFunction();
    current = compiler;

    if (type != TYPE_SCRIPT) {
        current->function->name = copyString(parser.previous.start, parser.previous.length);
    }

    // 栈槽0供虚拟机自己内部使用
    // 这里相当于加了一个在 0层深度的局部变量
    // 在运行时 栈底会存script function
    Local *local = &current->locals[current->localCount++];
    local->depth = 0;
    local->isCaptured = false;
    local->name.start = "";
    local->name.length = 0;
}

static void errorAt(Token *token, const char *message) {
    if (parser.panicMode) {
        return;
    }

    parser.panicMode = true;
    fprintf(stderr, "[line %d] Error", token->line);

    if (token->type == TOKEN_EOF) {
        fprintf(stderr, " at end");
    } else if (token->type == TOKEN_ERROR) {
        // Nothing.
    } else {
        fprintf(stderr, " at '%.*s'", token->length, token->start);
    }

    fprintf(stderr, ": %s\n", message);
    parser.hadError = true;
}

static void errorAtCurrent(const char *message) {
    errorAt(&parser.current, message);
}

static void error(const char *message) {
    errorAt(&parser.previous, message);
}

static void advance() {
    parser.previous = parser.current;

    while (true) {
        parser.current = scanToken();
        if (parser.current.type != TOKEN_ERROR) {
            break;
        }

        errorAtCurrent(parser.current.start);
    }
}

static void consume(TokenType type, const char *message) {
    if (parser.current.type == type) {
        advance();
        return;
    }

    errorAtCurrent(message);
}

static bool check(TokenType type) {
    return parser.current.type == type;
}

static bool match(TokenType type) {
    if (!check(type)) {
        return false;
    }
    advance();
    return true;
}


// ==== 生成字节码 ====
static void emitByte(uint8_t byte) {
    writeChunk(currentChunk(), byte, parser.previous.line);
}

static void emitBytes(uint8_t byte1, uint8_t byte2) {
    emitByte(byte1);
    emitByte(byte2);
}

static void emitReturn() {
    // 无论如何都返回一个null
    emitByte(OP_NIL);
    emitByte(OP_RETURN);
}

static ObjFunction *endCompiler() {
    emitReturn();
    ObjFunction *function = current->function;
#ifdef DEBUG_PRINT_CODE
    if (!parser.hadError) {
        disassembleChunk(currentChunk(), function->name != NULL ? function->name->chars : "<script>");
    }
#endif

    // Compiler永远都是局部变量 不用考虑释放的问题
    current = (Compiler *) current->enclosing;
    return function;
}

// 向常量池添加常量 并返回索引
static uint8_t makeConstant(Value value) {
    int idx = addConstant(currentChunk(), value);
    if (idx > UINT8_MAX) {
        error("Too many constants in one chunk.");
        return 0;
    }
    return (uint8_t) idx;
}

static void emitConstant(Value value) {
    emitBytes(OP_CONSTANT, makeConstant(value));
}


// 这个函数从当前的标识开始，解析给定优先级或更高优先级的任何表达式
// 假设我们正在处理 -a.b + c 这样的代码
// 如果我们调用parsePrecedence(PREC_ASSIGNMENT)，那么它就会解析整个表达式，因为+的优先级高于赋值。
// 如果我们调用parsePrecedence(PREC_UNARY)，它就会编译-a.b并停止。它不会径直解析+，因为加法的优先级比一元取负运算符要低。
static void parsePrecedence(Precedence precedence) {
    // 消费左侧操作数
    advance();
    ParseFn prefixRule = getRule(parser.previous.type)->prefix;
    if (prefixRule == NULL) {
        error("Expect expression.");
        return;
    }
    // 考虑 a * b = 1 + 2, 这种情况是不能赋值的
    bool canAssign = precedence <= PREC_ASSIGNMENT;
    // 生成左侧操作数的字节码
    prefixRule(canAssign);

    // eg: 1 + 2 * 3
    // 当前 precedence 是 '+' + 1, getRule(parser.current.type)->precedence 是 '*'
    // 因为 '+' + 1的优先级小于等于 '*', 所以 2 应当和 * 3结合, 所以需要进入循环 先生成乘法指令

    // 如果是 1 + 2 + 3
    // 那么 precedence 是 '+' + 1, getRule(parser.current.type)->precedence 是 '+'
    // 所以 2 应该和 1 + 先结合, 不用进入循环 先生成加法指令
    while (precedence <= getRule(parser.current.type)->precedence) {
        // 消费操作符
        advance();
        ParseFn infixRule = getRule(parser.previous.type)->infix;
        // 左侧操作数的字节码已经生成好了 现在生成右侧操作数的
        infixRule(canAssign);
    }

    if (canAssign && match(TOKEN_EQUAL)) {
        error("Invalid assignment target.");
    }
}

static void number(bool canAssign) {
    // number已经被消耗
    double value = strtod(parser.previous.start, NULL);
    emitConstant(NUMBER_VAL(value));
}

static void expression() {
    parsePrecedence(PREC_ASSIGNMENT);
}

static void grouping(bool canAssign) {
    // 就后端而言，分组表达式实际上没有任何意义。它的唯一功能是语法上的——它允许你在需要高优先级的地方插入一个低优先级的表达式。
    expression();
    consume(TOKEN_RIGHT_PAREN, "Expect ')' after expression.");
}

static void unary(bool canAssign) {
    // 前缀已经被消耗
    TokenType operatorType = parser.previous.type;

    // Compile the operand.
    parsePrecedence(PREC_UNARY);

    // Emit the operator instruction.
    switch (operatorType) {
        case TOKEN_BANG:
            emitByte(OP_NOT);
            break;
        case TOKEN_MINUS:
            emitByte(OP_NEGATE);
            break;
        default:
            return; // Unreachable.
    }
}

static void binary(bool canAssign) {
    TokenType operatorType = parser.previous.type;
    ParseRule *rule = getRule(operatorType);
    // 此时左侧的操作数字节码已经生成好了
    // 这里再生成右侧操作数的字节码
    parsePrecedence((Precedence) (rule->precedence + 1));

    // 生成符号字节码
    switch (operatorType) {
        case TOKEN_BANG_EQUAL:
            emitBytes(OP_EQUAL, OP_NOT);
            break;
        case TOKEN_EQUAL_EQUAL:
            emitByte(OP_EQUAL);
            break;
        case TOKEN_GREATER:
            emitByte(OP_GREATER);
            break;
        case TOKEN_GREATER_EQUAL:
            emitBytes(OP_LESS, OP_NOT);
            break;
        case TOKEN_LESS:
            emitByte(OP_LESS);
            break;
        case TOKEN_LESS_EQUAL:
            emitBytes(OP_GREATER, OP_NOT);
            break;
        case TOKEN_PLUS:
            emitByte(OP_ADD);
            break;
        case TOKEN_MINUS:
            emitByte(OP_SUBTRACT);
            break;
        case TOKEN_STAR:
            emitByte(OP_MULTIPLY);
            break;
        case TOKEN_SLASH:
            emitByte(OP_DIVIDE);
            break;
        default:
            return; // Unreachable.
    }
}

static void literal(bool canAssign) {
    switch (parser.previous.type) {
        case TOKEN_FALSE:
            emitByte(OP_FALSE);
            break;
        case TOKEN_NIL:
            emitByte(OP_NIL);
            break;
        case TOKEN_TRUE:
            emitByte(OP_TRUE);
            break;
        default:
            return; // Unreachable.
    }
}

static void string(bool canAssign) {
    // 略去两个双引号
    ObjString *str = copyString(parser.previous.start + 1, parser.previous.length - 2);
    Value value = OBJ_VAL(str);
    emitConstant(value);
}


static void printStatement() {
    expression();
    consume(TOKEN_SEMICOLON, "Expect ';' after value.");
    emitByte(OP_PRINT);
}

static void expressionStatement() {
    expression();
    consume(TOKEN_SEMICOLON, "Expect ';' after expression.");
    emitByte(OP_POP);
}

static void block() {
    while (!check(TOKEN_RIGHT_BRACE) && !check(TOKEN_EOF)) {
        declaration();
    }

    consume(TOKEN_RIGHT_BRACE, "Expect '}' after block.");
}

static void beginScope() {
    current->scopeDepth++;
}

static void endScope() {
    current->scopeDepth--;

    // 销毁局部变量
    while (current->localCount > 0 &&
           current->locals[current->localCount - 1].depth > current->scopeDepth) {
        // 被捕获了的局部变量 是需要被提升到堆中的 不能简单的pop
        if (current->locals[current->localCount - 1].isCaptured) {
            emitByte(OP_CLOSE_UPVALUE);
        } else {
            emitByte(OP_POP);
        }

        current->localCount--;
    }
}

static int emitJump(uint8_t instruction) {
    emitByte(instruction);
    // 这两个0xff是站位的, 因为此时还不知道ip到底要便宜多远
    emitByte(0xff);
    emitByte(0xff);
    // 返回占位符的索引
    return currentChunk()->count - 2;
}

static void patchJump(int offset) {
    // 当前ip - jump操作数处的ip - 操作数占用的2个字节
    int jump = currentChunk()->count - offset - 2;

    if (jump > UINT16_MAX) {
        error("Too much code to jump over.");
    }

    currentChunk()->code[offset] = (jump >> 8) & 0xff;
    currentChunk()->code[offset + 1] = jump & 0xff;
}

static void and(bool canAssign) {
    // 在这个方法被调用时，左侧的表达式已经被编译了。这意味着，在运行时，它的值将会在栈顶。
    // 如果这个值为假，我们就知道整个and表达式的结果一定是假，所以我们跳过右边的操作数，将左边的值作为整个表达式的结果。
    // 否则，我们就丢弃左值，计算右操作数，并将它作为整个and表达式的结果。
    /*
     * let op
     * jump if false
     * pop
     * right op
     * jump target
     */
    int endJump = emitJump(OP_JUMP_IF_FALSE);

    emitByte(OP_POP);
    parsePrecedence(PREC_AND);

    patchJump(endJump);
}

static void or(bool canAssign) {
    // 如果左侧操作数为真 就跳到结尾 返回左侧操作数
    // 如果作则操作数为假 就跳过一条jump指令 计算右侧操作数
    int elseJump = emitJump(OP_JUMP_IF_FALSE);
    int endJump = emitJump(OP_JUMP);

    patchJump(elseJump);
    emitByte(OP_POP);

    parsePrecedence(PREC_OR);
    patchJump(endJump);
}

static void ifStatement() {
    consume(TOKEN_LEFT_PAREN, "Expect '(' after 'if'.");
    // 结果留在栈顶
    expression();
    consume(TOKEN_RIGHT_PAREN, "Expect ')' after condition.");

    /*
     * jump_if_false @else
     *      pop
     *      xxx
     *      xxx
     *      jump @end
     * @else
     *      pop
     *      xxx
     *      xxx
     * @end
     *
     */
    int thenJump = emitJump(OP_JUMP_IF_FALSE);
    // 弹出栈顶的表达式值
    emitByte(OP_POP);
    statement();
    int elseJump = emitJump(OP_JUMP);
    // 回填jump的操作数
    patchJump(thenJump);
    emitByte(OP_POP);
    if (match(TOKEN_ELSE)) {
        statement();
    }
    patchJump(elseJump);
}

static void emitLoop(int loopStart) {
    // 往回跳
    emitByte(OP_LOOP);

    int offset = currentChunk()->count - loopStart + 2;
    if (offset > UINT16_MAX) {
        error("Loop body too large.");
    }

    emitByte((offset >> 8) & 0xff);
    emitByte(offset & 0xff);
}

static void whileStatement() {
    // 循环要跳回来的位置
    int loopStart = currentChunk()->count;

    consume(TOKEN_LEFT_PAREN, "Expect '(' after 'while'.");
    expression();
    consume(TOKEN_RIGHT_PAREN, "Expect ')' after condition.");

    int exitJump = emitJump(OP_JUMP_IF_FALSE);
    emitByte(OP_POP);
    statement();

    emitLoop(loopStart);

    patchJump(exitJump);
    emitByte(OP_POP);
}

static void forStatement() {
    beginScope();
    consume(TOKEN_LEFT_PAREN, "Expect '(' after 'for'.");
    // 初始化子句
    if (match(TOKEN_SEMICOLON)) {
        // No initializer.
    } else if (match(TOKEN_VAR)) {
        varDeclaration();
    } else {
        expressionStatement();
    }

    int loopStart = currentChunk()->count;

    // 条件子句
    int exitJump = -1;
    if (!match(TOKEN_SEMICOLON)) {
        expression();
        consume(TOKEN_SEMICOLON, "Expect ';' after loop condition.");

        // Jump out of the loop if the condition is false.
        exitJump = emitJump(OP_JUMP_IF_FALSE);
        emitByte(OP_POP); // Condition.
    }

    // 增量子句
    // 增量子句应该在 statement() 之后再执行
    // 但因为是单边编译器, 所以字节码必须在这里生成
    if (!match(TOKEN_RIGHT_PAREN)) {
        // 跳到statement() 执行
        int bodyJump = emitJump(OP_JUMP);
        int incrementStart = currentChunk()->count;
        expression();
        emitByte(OP_POP);
        consume(TOKEN_RIGHT_PAREN, "Expect ')' after for clauses.");
        // 跳到循环开头
        emitLoop(loopStart);
        loopStart = incrementStart;
        patchJump(bodyJump);
    }

    statement();
    // 如果有增量子句的话 这里是跳到增量子句 而不是循环开始
    emitLoop(loopStart);

    if (exitJump != -1) {
        patchJump(exitJump);
        emitByte(OP_POP); // Condition.
    }

    endScope();
}

static void returnStatement() {
    if (current->type == TYPE_SCRIPT) {
        error("Can't return from top-level code.");
    }
    if (match(TOKEN_SEMICOLON)) {
        // 这里会压入null作为返回值
        emitReturn();
    } else {
        expression();
        consume(TOKEN_SEMICOLON, "Expect ';' after return value.");
        emitByte(OP_RETURN);
    }
}

static void statement() {
    if (match(TOKEN_PRINT)) {
        printStatement();
    } else if (match(TOKEN_FOR)) {
        forStatement();
    } else if (match(TOKEN_IF)) {
        ifStatement();
    } else if (match(TOKEN_RETURN)) {
        returnStatement();
    } else if (match(TOKEN_WHILE)) {
        whileStatement();
    } else if (match(TOKEN_LEFT_BRACE)) {
        beginScope();
        block();
        endScope();
    } else {
        expressionStatement();
    }

}

static void synchronize() {
    parser.panicMode = false;

    while (parser.current.type != TOKEN_EOF) {
        if (parser.previous.type == TOKEN_SEMICOLON) {
            return;
        }
        switch (parser.current.type) {
            case TOKEN_CLASS:
            case TOKEN_FUN:
            case TOKEN_VAR:
            case TOKEN_FOR:
            case TOKEN_IF:
            case TOKEN_WHILE:
            case TOKEN_PRINT:
            case TOKEN_RETURN:
                return;

            default:; // Do nothing.
        }

        advance();
    }
}


static uint8_t identifierConstant(Token *name) {
    // 创建一个ObjString* 写入到常量池, 返回索引
    return makeConstant(OBJ_VAL(copyString(name->start, name->length)));
}

static bool identifiersEqual(Token *a, Token *b) {
    if (a->length != b->length) {
        return false;
    }
    return memcmp(a->start, b->start, a->length) == 0;
}

static void addLocal(Token name) {
    if (current->localCount == UINT8_COUNT) {
        error("Too many local variables in function.");
        return;
    }

    Local *local = &current->locals[current->localCount++];
    local->name = name;
    // -1 表示已经声明了该变量 仅仅把变量名加到了作用域中
    // 但还没进行初始化 不能使用
    local->depth = -1;
    local->isCaptured = false;
}

static void declareVariable() {
    if (current->scopeDepth == 0) {
        // 全局作用域 直接退出
        return;
    }
    Token *name = &parser.previous;
    // 检测 同一个作用域内不能有同名变量
    for (int i = current->localCount - 1; i >= 0; i--) {
        Local *local = &current->locals[i];
        if (local->depth != -1 && local->depth < current->scopeDepth) {
            // 找到外层作用域了 说明当前作用域没有同名变量
            break;
        }

        if (identifiersEqual(name, &local->name)) {
            error("Already a variable with this name in this scope.");
        }
    }

    addLocal(*name);
}

static uint8_t parseVariable(const char *errorMessage) {
    consume(TOKEN_IDENTIFIER, errorMessage);
    declareVariable();
    if (current->scopeDepth > 0) {
        // 在局部作用域中 不把变量名放到常量池中
        return 0;
    }
    return identifierConstant(&parser.previous);
}

static void markInitialized() {
    if (current->scopeDepth == 0) {
        // 没有全局变量需要被初始化 直接退出
        return;
    }
    current->locals[current->localCount - 1].depth = current->scopeDepth;
}

static void defineVariable(uint8_t global) {
    if (current->scopeDepth > 0) {
        // 初始化完成 设置变量真实的作用域深度
        markInitialized();
        // 在局部作用域中 不生成全局变量指令
        return;
    }
    emitBytes(OP_DEFINE_GLOBAL, global);
}

static void varDeclaration() {
    uint8_t global = parseVariable("Expect variable name.");

    if (match(TOKEN_EQUAL)) {
        // 如果是局部变量 那么表达式计算完之后 栈顶的值就是局部变量的值
        expression();
    } else {
        emitByte(OP_NIL);
    }
    consume(TOKEN_SEMICOLON, "Expect ';' after variable declaration.");

    defineVariable(global);
}

// 返回局部变量在 局部数组中的索引
// 变量在局部变量数组中的索引与其在栈中的槽位相同
static int resolveLocal(Compiler *compiler, Token *name) {
    for (int i = compiler->localCount - 1; i >= 0; i--) {
        Local *local = &compiler->locals[i];
        if (identifiersEqual(name, &local->name)) {
            if (local->depth == -1) {
                error("Can't read local variable in its own initializer.");
            }
            return i;
        }
    }

    return -1;
}

/**
 * 为当前函数添加一个upvalue
 * upvalue数组的索引 与运行时ObjClosure中upvalue所在的索引相匹配
 * @param compiler
 * @param index     被捕获的局部变量的栈槽索引
 * @param isLocal
 * @return 新创建的upvalue在upvalue数组中的索引
 */
static int addUpvalue(Compiler *compiler, uint8_t index, bool isLocal) {
    int upvalueCount = compiler->function->upvalueCount;

    // 一个闭包可能会多次引用外围函数中的同一个变量
    // 这种情况不需要重复创建upvalue
    for (int i = 0; i < upvalueCount; i++) {
        Upvalue *upvalue = &compiler->upvalues[i];
        if (upvalue->index == index && upvalue->isLocal == isLocal) {
            return i;
        }
    }

    if (upvalueCount == UINT8_COUNT) {
        error("Too many closure variables in function.");
        return 0;
    }

    compiler->upvalues[upvalueCount].isLocal = isLocal;
    compiler->upvalues[upvalueCount].index = index;
    return compiler->function->upvalueCount++;
}

// 查找在任何外围函数中声明的局部变量。如果找到了，就会返回该变量的“上值索引”
static int resolveUpvalue(Compiler *compiler, Token *name) {
    if (compiler->enclosing == NULL) return -1;

    // 从上一层捕获 局部变量
    int local = resolveLocal((Compiler *) compiler->enclosing, name);
    if (local != -1) {
        Compiler *enclosing = (Compiler *) compiler->enclosing;
        enclosing->locals[local].isCaptured = true;
        return addUpvalue(compiler, (uint8_t) local, true);
    }

    // 如果上一层没捕获到 就捕获上一层的upvalue
    int upvalue = resolveUpvalue((Compiler *) compiler->enclosing, name);
    if (upvalue != -1) {
        return addUpvalue(compiler, (uint8_t) upvalue, false);
    }

    return -1;
}

static void namedVariable(Token name, bool canAssign) {
    uint8_t getOp, setOp;
    int arg = resolveLocal(current, &name);
    if (arg != -1) {
        getOp = OP_GET_LOCAL;
        setOp = OP_SET_LOCAL;
    } else if ((arg = resolveUpvalue(current, &name)) != -1) {
        getOp = OP_GET_UPVALUE;
        setOp = OP_SET_UPVALUE;
    } else {
        arg = identifierConstant(&name);
        getOp = OP_GET_GLOBAL;
        setOp = OP_SET_GLOBAL;
    }
    // 赋值 setter
    if (canAssign && match(TOKEN_EQUAL)) {
        expression();
        emitBytes(setOp, (uint8_t) arg);
    } else {
        // getter
        emitBytes(getOp, (uint8_t) arg);
    }
}

static void variable(bool canAssign) {
    namedVariable(parser.previous, canAssign);
}

static void function(FunctionType type) {
    Compiler compiler;
    initCompiler(&compiler, type);
    // 这是增加的是当前啊compiler的scope
    // 函数中永远都是局部变量 所以没有endScope()
    beginScope(); // [no-end-scope]

    consume(TOKEN_LEFT_PAREN, "Expect '(' after function name.");
    if (!check(TOKEN_RIGHT_PAREN)) {
        do {
            current->function->arity++;
            if (current->function->arity > 255) {
                errorAtCurrent("Can't have more than 255 parameters.");
            }
            uint8_t constant = parseVariable("Expect parameter name.");
            defineVariable(constant);
        } while (match(TOKEN_COMMA));
    }
    consume(TOKEN_RIGHT_PAREN, "Expect ')' after parameters.");
    consume(TOKEN_LEFT_BRACE, "Expect '{' before function body.");
    block();

    ObjFunction *function = endCompiler();
    emitBytes(OP_CLOSURE, makeConstant(OBJ_VAL(function)));

    for (int i = 0; i < function->upvalueCount; i++) {
        emitByte(compiler.upvalues[i].isLocal ? 1 : 0);
        emitByte(compiler.upvalues[i].index);
    }
}

static void funDeclaration() {
    uint8_t global = parseVariable("Expect function name.");
    markInitialized();
    // 函数对象留在栈顶
    function(TYPE_FUNCTION);
    defineVariable(global);
}

static uint8_t argumentList() {
    uint8_t argCount = 0;
    // 每个参数表达式都会生成代码，将其值留在栈中
    if (!check(TOKEN_RIGHT_PAREN)) {
        do {
            expression();
            if (argCount == 255) {
                error("Can't have more than 255 arguments.");
            }
            argCount++;
        } while (match(TOKEN_COMMA));
    }
    consume(TOKEN_RIGHT_PAREN, "Expect ')' after arguments.");
    return argCount;
}

static void call(bool canAssign) {
    uint8_t argCount = argumentList();
    emitBytes(OP_CALL, argCount);
}

static void declaration() {
    if (match(TOKEN_FUN)) {
        funDeclaration();
    } else if (match(TOKEN_VAR)) {
        varDeclaration();
    } else {
        statement();
    }
    if (parser.panicMode) {
        synchronize();
    }
}


ObjFunction *compile(const char *source) {
    parser.hadError = false;
    parser.panicMode = false;
    Compiler compiler;
    initCompiler(&compiler, TYPE_SCRIPT);
    initScanner(source);
    advance();

    while (!match(TOKEN_EOF)) {
        declaration();
    }

    ObjFunction *function = endCompiler();
    log("======== compile done ========\n");
    return parser.hadError ? NULL : function;
}

void markCompilerRoots() {
    Compiler *compiler = current;
    while (compiler != NULL) {
        markObject((Obj *) compiler->function);
        compiler = (Compiler *) compiler->enclosing;
    }
}