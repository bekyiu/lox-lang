from typing import Union

from interpreter.error import ParseException
from interpreter.expr import Expr, Binary, Unary, Literal, Grouping
from interpreter.lox import Lox
from interpreter.token import Token, TokenType

"""
每个规则仅匹配其当前优先级或更高优先级的表达式
表达式优先级自上而下递增

expression     → equality ;
equality       → comparison ( ( "!=" | "==" ) comparison )* ;
comparison     → term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
term           → factor ( ( "-" | "+" ) factor )* ;
factor         → unary ( ( "/" | "*" ) unary )* ;
unary          → ( "!" | "-" ) unary
               | primary ;
primary        → NUMBER | STRING | "true" | "false" | "nil"
               | "(" expression ")" ;
"""


class Parser:
    tokens: list[Token]
    # 当前正在解析的token
    current: int

    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Union[Expr, None]:
        try:
            return self._parse_expression()
        except ParseException as e:
            return None

    def _parse_expression(self) -> Expr:
        return self._parse_equality()

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
        return self._parse_primary()

    def _parse_primary(self) -> Expr:
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
