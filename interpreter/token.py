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

    EOF = 400


class Token:
    type: TokenType
    lexeme: str
    literal: object
    line: int

    def __init__(self, type, lexeme, literal, line):
        self.type = type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __repr__(self):
        return f'{self.type} {self.lexeme} {self.literal}'
