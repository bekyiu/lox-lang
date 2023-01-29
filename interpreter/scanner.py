from interpreter.lox import Lox
from interpreter.token import Token, TokenType


class Scanner:
    # 源代码
    source: str
    # 结果列表
    tokens: list[Token]
    # 被扫描token的第一个字符
    start: int
    # 当前指向的字符
    current: int
    # 当前扫描token的行号
    line: int

    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> list[Token]:
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()

        eof_token = Token(TokenType.EOF, "", None, self.line)
        self.tokens.append(eof_token)
        return self.tokens

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _scan_token(self) -> None:
        ch = self._advance()
        # white
        if ch == ' ' or ch == '\r' or ch == '\t':
            return
        if ch == '\n':
            self.line += 1
            return
        # single char token
        if ch == '(':
            self._add_token(TokenType.LEFT_PAREN)
            return
        if ch == ')':
            self._add_token(TokenType.RIGHT_PAREN)
            return
        if ch == '{':
            self._add_token(TokenType.LEFT_BRACE)
            return
        if ch == '}':
            self._add_token(TokenType.RIGHT_BRACE)
            return
        if ch == ',':
            self._add_token(TokenType.COMMA)
            return
        if ch == '.':
            self._add_token(TokenType.DOT)
            return
        if ch == '-':
            self._add_token(TokenType.MINUS)
            return
        if ch == '+':
            self._add_token(TokenType.PLUS)
            return
        if ch == ';':
            self._add_token(TokenType.SEMICOLON)
            return
        if ch == '*':
            self._add_token(TokenType.STAR)
            return
        # 2 char token
        if ch == '!':
            self._add_token(self._match_type('=', TokenType.BANG_EQUAL, TokenType.BANG))
            return
        if ch == '=':
            self._add_token(self._match_type('=', TokenType.EQUAL_EQUAL, TokenType.EQUAL))
            return
        if ch == '<':
            self._add_token(self._match_type('=', TokenType.LESS_EQUAL, TokenType.LESS))
            return
        if ch == '>':
            self._add_token(self._match_type('=', TokenType.GREATER_EQUAL, TokenType.GREATER))
            return
        # other
        if ch == '/':
            self._strip_comment() if self._is_match('/') else self._add_token(TokenType.SLASH)
            return
        if ch == '"':
            self._strip_string()
            return
        if ch.isdigit():
            self._strip_number()
            return
        if ch.isalpha() or ch == '_':
            self._strip_identifier()
            return

        Lox.error(self.line, ch, 'unexpected character')

    def _advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        return ch

    def _add_token(self, type: TokenType, literal: object = None) -> None:
        text = self.source[self.start:self.current]
        token = Token(type, text, literal, self.line)
        self.tokens.append(token)

    def _peek(self) -> str:
        if self._is_at_end():
            return '\0'
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _is_match(self, expected: str) -> bool:
        ch = self._peek()
        return ch == expected

    def _match_type(self, expected: str, true: TokenType, false: TokenType) -> TokenType:
        ret = self._is_match(expected)
        if ret:
            self.current += 1
            return true
        return false

    def _strip_comment(self) -> None:
        # // foo
        while (not self._is_at_end()) and (self._peek() != '\n'):
            self._advance()

    def _strip_string(self) -> None:
        # todo 报错 比如字符串没有闭合 或者留到语法分析?
        # "foo"
        while (not self._is_at_end()) and (self._peek() != '"'):
            if self._peek() == '\n':
                self.line += 1
            self._advance()
        # end "
        self._advance()
        value = self.source[self.start + 1:self.current - 1]
        self._add_token(TokenType.STRING, value)

    def _strip_number(self) -> None:
        # 123
        # 123.55
        # todo 考虑负数, is end 判断
        while self._peek().isdigit():
            self._advance()

        is_float = False
        # maybe .
        if self._peek() == '.' and self._peek_next().isdigit():
            is_float = True
            # skip .
            self._advance()
            while self._peek().isdigit():
                self._advance()

        value = self.source[self.start:self.current]
        value = float(value) if is_float else int(value)
        self._add_token(TokenType.NUMBER, value)

    def _strip_identifier(self) -> None:
        ch = self._peek()
        while ch.isalnum() or ch == '_':
            self._advance()
            ch = self._peek()

        text = self.source[self.start:self.current]
        type = TokenType.KEYWORD_MAP.get(text, TokenType.IDENTIFIER)
        self._add_token(type)
