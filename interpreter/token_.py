from __future__ import annotations
from enum import Enum, unique


@unique
class TokenType(Enum):
    # Single-character tokens.
    LEFT_PAREN = 0
    RIGHT_PAREN = 1
    LEFT_BRACE = 2
    RIGHT_BRACE = 3
    COMMA = 4
    DOT = 5
    MINUS = 6
    PLUS = 7
    SEMICOLON = 8
    SLASH = 9
    STAR = 10

    # One or two character tokens.
    BANG = 100
    BANG_EQUAL = 101
    EQUAL = 102
    EQUAL_EQUAL = 103
    GREATER = 104
    GREATER_EQUAL = 105
    LESS = 106
    LESS_EQUAL = 107

    # Literals.
    IDENTIFIER = 200
    STRING = 201
    NUMBER = 202

    # Keywords.
    AND = 300
    CLASS = 301
    ELSE = 302
    FALSE = 303
    FUN = 304
    FOR = 305
    IF = 306
    NIL = 307
    OR = 308
    PRINT = 309
    RETURN = 310
    SUPER = 311
    THIS = 312
    TRUE = 313
    VAR = 314
    WHILE = 315
    BREAK = 316
    CONTINUE = 317

    EOF = 400

    SYMBOL_MAP: dict[str, TokenType]
    KEYWORD_MAP: dict[str, TokenType]

    @staticmethod
    def static_init():
        TokenType.SYMBOL_MAP = {
            '(': TokenType.LEFT_PAREN,
            ')': TokenType.RIGHT_PAREN,
            '{': TokenType.LEFT_BRACE,
            '}': TokenType.RIGHT_BRACE,
            ',': TokenType.COMMA,
            '.': TokenType.DOT,
            '-': TokenType.MINUS,
            '+': TokenType.PLUS,
            ';': TokenType.SEMICOLON,
            '/': TokenType.SLASH,
            '*': TokenType.STAR,

            '!': TokenType.BANG,
            '!=': TokenType.BANG_EQUAL,
            '=': TokenType.EQUAL,
            '==': TokenType.EQUAL_EQUAL,
            '>': TokenType.GREATER,
            '>=': TokenType.GREATER_EQUAL,
            '<': TokenType.LESS,
            '<=': TokenType.LESS_EQUAL,
        }

        TokenType.KEYWORD_MAP = {
            "and": TokenType.AND,
            "class": TokenType.CLASS,
            "else": TokenType.ELSE,
            "false": TokenType.FALSE,
            "fun": TokenType.FUN,
            "for": TokenType.FOR,
            "if": TokenType.IF,
            "nil": TokenType.NIL,
            "or": TokenType.OR,
            "print": TokenType.PRINT,
            "return": TokenType.RETURN,
            "super": TokenType.SUPER,
            "this": TokenType.THIS,
            "true": TokenType.TRUE,
            "var": TokenType.VAR,
            "while": TokenType.WHILE,
            "break": TokenType.BREAK,
            "continue": TokenType.CONTINUE,
        }

    @staticmethod
    def is_keyword(s: str) -> bool:
        return s in TokenType.KEYWORD_MAP.keys()


TokenType.static_init()


class Token:
    # token类型
    type: TokenType
    # token的文本内容
    lexeme: str
    # 字符串和数字的真实值
    literal: object
    # 行号
    line: int

    def __init__(self, type, lexeme, literal, line):
        self.type = type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __repr__(self):
        return f'{self.type} {self.lexeme} {self.literal}'
