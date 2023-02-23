from interpreter.error import ParseException
from interpreter.expr import Expr, Binary, Unary, Literal, Grouping, Variable, Assign, Logical, Call, Get, Set, This, \
    Super
from interpreter.lox import Lox
from interpreter.stmt import Stmt, Print, Expression, Var, Block, If, While, Break, Continue, Function, Return, Class
from interpreter.token_ import Token, TokenType

"""
每个规则仅匹配其当前优先级或更高优先级的表达式
表达式优先级自上而下递增

expression     → assignment ;
expression     → assignment ;
assignment     → ( call "." )? IDENTIFIER "=" assignment
               | logic_or ;
logic_or       → logic_and ( "or" logic_and )* ;
logic_and      → equality ( "and" equality )* ;
equality       → comparison ( ( "!=" | "==" ) comparison )* ;
comparison     → term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
term           → factor ( ( "-" | "+" ) factor )* ;
factor         → unary ( ( "/" | "*" ) unary )* ;
unary          → ( "!" | "-" ) unary
               | primary ;
unary          → ( "!" | "-" ) unary | call ;

call           → primary ( "(" arguments? ")" | "." IDENTIFIER )* ;

primary        → "true" | "false" | "nil" | "this"
               | NUMBER | STRING | IDENTIFIER | "(" expression ")"
               | "super" "." IDENTIFIER ;

arguments      → expression ( "," expression )* ;
"""

"""
program        → declaration* EOF ;

declaration    → classDecl
               | funDecl
               | varDecl
               | statement ;

classDecl      → "class" IDENTIFIER ( "<" IDENTIFIER )?
                 "{" function* "}" ;


statement      → exprStmt
               | breakStmt
               | continueStmt
               | forStmt
               | ifStmt
               | printStmt
               | returnStmt
               | whileStmt
               | block ;

returnStmt     → "return" expression? ";" ;
               
breakStmt      → "break" ";" ;
continueStmt   → "continue" ";" ;

forStmt        → "for" "(" ( varDecl | exprStmt | ";" )
                 expression? ";"
                 expression? ")" statement ;

whileStmt      → "while" "(" expression ")" statement ;

ifStmt         → "if" "(" expression ")" statement
               ( "else" statement )? ;

block          → "{" declaration* "}" ;

exprStmt       → expression ";" ;
printStmt      → "print" expression ";" ;
varDecl        → "var" IDENTIFIER ( "=" expression )? ";" ;

funDecl        → "fun" function ;
function       → IDENTIFIER "(" parameters? ")" block ;
parameters     → IDENTIFIER ( "," IDENTIFIER )* ;
"""


class Parser:
    tokens: list[Token]
    # 当前正在解析的token
    current: int

    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> list[Stmt]:
        stmts = []
        while not self._is_at_end():
            stmts.append(self._parse_declaration())
        return stmts

    def _parse_declaration(self) -> Stmt:
        try:
            if self._match_any_type(TokenType.CLASS):
                return self._parse_class_declaration()
            if self._match_any_type(TokenType.FUN):
                return self._parse_function("function")
            if self._match_any_type(TokenType.VAR):
                return self._parse_var_declaration()
            return self._parse_statement()
        except ParseException as e:
            self._synchronize()
            return None

    def _parse_class_declaration(self) -> Stmt:
        name = self._ensure(TokenType.IDENTIFIER, 'expect class name')

        super_class = None
        if self._match_any_type(TokenType.LESS):
            self._ensure(TokenType.IDENTIFIER, 'expect supper class name')
            super_class = Variable(self._peek_pre())

        self._ensure(TokenType.LEFT_BRACE, "expect '{' before class body")

        methods = []
        while not self._is_match(TokenType.RIGHT_BRACE) and not self._is_at_end():
            m = self._parse_function("method")
            methods.append(m)

        self._ensure(TokenType.RIGHT_BRACE, "expect '}' after class body")
        return Class(name, super_class, methods)

    def _parse_function(self, kind: str) -> Stmt:
        name = self._ensure(TokenType.IDENTIFIER, f'expect {kind} name')
        self._ensure(TokenType.LEFT_PAREN, f"expect '(' after {kind} name")
        params = []
        while not self._is_match(TokenType.RIGHT_PAREN):
            if len(params) >= 255:
                self._error(self._peek(), 'can not have more than 255 parameters')

            params.append(self._ensure(TokenType.IDENTIFIER, 'expect parameter name'))
            self._match_any_type(TokenType.COMMA)

        self._ensure(TokenType.RIGHT_PAREN, "expect ')' after parameters")
        self._ensure(TokenType.LEFT_BRACE, f"expect {'{'} before {kind} body")
        body = self._parse_block()
        return Function(name, params, body)

    def _parse_var_declaration(self) -> Stmt:
        token = self._ensure(TokenType.IDENTIFIER, 'Expect a identifier after var.')
        initializer = None
        if self._match_any_type(TokenType.EQUAL):
            initializer = self._parse_expression()
        self._ensure(TokenType.SEMICOLON, "expected ';' after var statement")
        return Var(token, initializer)

    def _parse_statement(self) -> Stmt:
        if self._match_any_type(TokenType.RETURN):
            return self._parse_return()
        if self._match_any_type(TokenType.BREAK):
            return self._parse_break()
        if self._match_any_type(TokenType.CONTINUE):
            return self._parse_continue()
        if self._match_any_type(TokenType.FOR):
            return self._parse_for()
        if self._match_any_type(TokenType.WHILE):
            return self._parse_while()
        if self._match_any_type(TokenType.IF):
            return self._parse_if()
        if self._match_any_type(TokenType.PRINT):
            return self._parse_print()
        if self._match_any_type(TokenType.LEFT_BRACE):
            return Block(self._parse_block())

        return self._parse_expr_stmt()

    def _parse_return(self) -> Stmt:
        keyword = self._peek_pre()
        value = None
        if not self._is_match(TokenType.SEMICOLON):
            value = self._parse_expression()
        self._ensure(TokenType.SEMICOLON, "expect ';' after return value")
        return Return(keyword, value)

    def _parse_break(self) -> Stmt:
        token = self._peek_pre()
        self._ensure(TokenType.SEMICOLON, "expect ';' after break")
        return Break(token)

    def _parse_continue(self) -> Stmt:
        token = self._peek_pre()
        raise self._error(token, 'not impl now')
        # self._ensure(TokenType.SEMICOLON, "expect ';' after continue")
        # return Continue(token)

    # 语法糖 没有真正的For节点
    def _parse_for(self) -> Stmt:
        self._ensure(TokenType.LEFT_PAREN, "expect '(' after for")
        initializer = None
        if self._match_any_type(TokenType.VAR):
            initializer = self._parse_var_declaration()
        elif self._match_any_type(TokenType.SEMICOLON):
            initializer = None
        else:
            initializer = self._parse_expr_stmt()

        condition = Literal(True)
        if not self._is_match(TokenType.SEMICOLON):
            condition = self._parse_expression()
        self._ensure(TokenType.SEMICOLON, "expect ';' after condition")

        increment = None
        if not self._is_match(TokenType.RIGHT_PAREN):
            increment = self._parse_expression()
        self._ensure(TokenType.RIGHT_PAREN, "expect ')' after clauses")

        body = self._parse_statement()

        """
        de-sugaring to
        {
            initializer
            while(condition) {
                body
                increment
            }
        }
        """
        if increment is not None:
            body = Block([body, Expression(increment)])
        body = While(condition, body)
        if initializer is not None:
            body = Block([initializer, body])
        return body

    def _parse_while(self) -> Stmt:
        self._ensure(TokenType.LEFT_PAREN, "expect '(' after while")
        condition = self._parse_expression()
        self._ensure(TokenType.RIGHT_PAREN, "expect ')' after condition")
        body = self._parse_statement()
        return While(condition, body)

    def _parse_if(self) -> Stmt:
        self._ensure(TokenType.LEFT_PAREN, "expect '(' after if")
        condition = self._parse_expression()
        self._ensure(TokenType.RIGHT_PAREN, "expect ')' after condition")
        then_branch = self._parse_statement()
        else_branch = None
        if self._match_any_type(TokenType.ELSE):
            else_branch = self._parse_statement()
        return If(condition, then_branch, else_branch)

    def _parse_block(self) -> list[Stmt]:
        stmts = []
        while not self._is_at_end() and not self._is_match(TokenType.RIGHT_BRACE):
            stmts.append(self._parse_declaration())
        self._ensure(TokenType.RIGHT_BRACE, "expected '}' after block")
        return stmts

    def _parse_print(self) -> Stmt:
        expr = self._parse_expression()
        self._ensure(TokenType.SEMICOLON, "expected ';' after print statement")
        return Print(expr)

    def _parse_expr_stmt(self) -> Stmt:
        expr = self._parse_expression()
        self._ensure(TokenType.SEMICOLON, "expected ';' after expression")
        return Expression(expr)

    def _parse_expression(self) -> Expr:
        return self._parse_assigment()

    def _parse_assigment(self) -> Expr:
        expr = self._parse_or()
        if self._match_any_type(TokenType.EQUAL):
            equal = self._peek_pre()
            value = self._parse_assigment()
            if isinstance(expr, Variable):
                # = 左边是一个左值, 表明表达式的结果要存在哪, 而不对自己进行求值
                return Assign(expr.name, value)
            if isinstance(expr, Get):
                # a.b.c = d
                # a.b.c都是get 然后被包装成了set
                return Set(expr.object, expr.name, value)
            self._error(equal, 'Invalid assigment target')
        return expr

    def _parse_or(self) -> Expr:
        left = self._parse_and()
        while self._match_any_type(TokenType.OR):
            op = self._peek_pre()
            right = self._parse_and()
            left = Logical(left, op, right)
        return left

    def _parse_and(self) -> Expr:
        left = self._parse_equality()
        while self._match_any_type(TokenType.AND):
            op = self._peek_pre()
            right = self._parse_equality()
            left = Logical(left, op, right)
        return left

    def _parse_equality(self) -> Expr:
        expr = self._parse_comparison()
        while self._match_any_type(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            op = self._peek_pre()
            right = self._parse_comparison()
            # 上轮的expr是这一轮的左子树
            expr = Binary(expr, op, right)
        return expr

    def _parse_comparison(self) -> Expr:
        expr = self._parse_term()
        while self._match_any_type(TokenType.GREATER, TokenType.GREATER_EQUAL,
                                   TokenType.LESS, TokenType.LESS_EQUAL):
            op = self._peek_pre()
            right = self._parse_term()
            expr = Binary(expr, op, right)
        return expr

    def _parse_term(self) -> Expr:
        expr = self._parse_factor()
        while self._match_any_type(TokenType.PLUS, TokenType.MINUS):
            op = self._peek_pre()
            right = self._parse_factor()
            expr = Binary(expr, op, right)
        return expr

    def _parse_factor(self) -> Expr:
        expr = self._parse_unary()
        while self._match_any_type(TokenType.STAR, TokenType.SLASH):
            op = self._peek_pre()
            right = self._parse_unary()
            expr = Binary(expr, op, right)
        return expr

    def _parse_unary(self) -> Expr:
        if self._match_any_type(TokenType.MINUS, TokenType.BANG):
            op = self._peek_pre()
            right = self._parse_unary()
            return Unary(op, right)
        return self._parse_call()

    def _parse_call(self) -> Expr:
        expr = self._parse_primary()
        while True:
            # 可能有这种情况 f()()
            # a.b
            # a.b(c)
            if self._match_any_type(TokenType.LEFT_PAREN):
                expr = self._parse_finish_call(expr)
            elif self._match_any_type(TokenType.DOT):
                name = self._ensure(TokenType.IDENTIFIER, "expect property name after '.'")
                expr = Get(expr, name)
            else:
                break

        return expr

    def _parse_finish_call(self, callee: Expr) -> Expr:
        args = []
        while not self._is_match(TokenType.RIGHT_PAREN):
            if len(args) >= 255:
                self._error(self._peek(), 'can not have more than 255 arguments')

            args.append(self._parse_expression())
            self._match_any_type(TokenType.COMMA)
        paren = self._ensure(TokenType.RIGHT_PAREN, "expect ')' after arguments")
        return Call(callee, paren, args)

    def _parse_primary(self) -> Expr:
        if self._match_any_type(TokenType.THIS):
            return This(self._peek_pre())
        if self._match_any_type(TokenType.FALSE):
            return Literal(False)
        if self._match_any_type(TokenType.TRUE):
            return Literal(True)
        if self._match_any_type(TokenType.NIL):
            return Literal(None)
        if self._match_any_type(TokenType.NUMBER, TokenType.STRING):
            return Literal(self._peek_pre().literal)
        if self._match_any_type(TokenType.LEFT_PAREN):
            expr = self._parse_expression()
            self._ensure(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)
        if self._match_any_type(TokenType.IDENTIFIER):
            return Variable(self._peek_pre())
        if self._match_any_type(TokenType.SUPER):
            keyword = self._peek_pre()
            self._ensure(TokenType.DOT, "expect '.' after super")
            method = self._ensure(TokenType.IDENTIFIER, 'expect super class method name')
            return Super(keyword, method)
        raise self._error(self._peek(), 'expect expression.')

    def _ensure(self, type: TokenType, error_msg: str) -> Token:
        if self._is_match(type):
            return self._advance()
        raise self._error(self._peek(), error_msg)

    def _error(self, token: Token, msg: str) -> ParseException:
        Lox.error(token=token, message=msg)
        return ParseException(msg)

    def _match_any_type(self, *types) -> bool:
        for type in types:
            ret = self._is_match(type)
            if ret:
                self._advance()
                return True
        return False

    def _is_match(self, expected: TokenType) -> bool:
        t = self._peek()
        return t.type == expected

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._peek_pre()

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _peek_pre(self) -> Token:
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    # 丢弃当前token 直到(差不多)下一条语句
    def _synchronize(self) -> None:
        self._advance()
        while not self._is_at_end():
            if self._peek_pre() == TokenType.SEMICOLON:
                return
            t = self._peek().type
            if t == TokenType.CLASS or \
                    t == TokenType.FUN or \
                    t == TokenType.VAR or \
                    t == TokenType.FOR or \
                    t == TokenType.IF or \
                    t == TokenType.WHILE or \
                    t == TokenType.PRINT or \
                    t == TokenType.RETURN:
                return
            self._advance()
