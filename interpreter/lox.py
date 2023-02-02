import sys

from interpreter.error import RuntimeException
from interpreter.token import Token


class Lox:
    had_error: bool = False
    had_runtime_error: bool = False

    @staticmethod
    def start() -> None:
        Lox.run_file()

    @staticmethod
    def log(*args, sep: str = ' ', end: str = '\n'):
        print(*args, sep=sep, end=end)

    @staticmethod
    def error(*,
              line: int = 0,
              where: str = 0,
              message: str = 0,
              token: Token = None) -> None:
        Lox.had_error = True
        if token is None:
            Lox.log(f'line: {line}, at[{where}]: {message}')
        else:
            Lox.log(f'line: {token.line}, at[{token.lexeme}]: {message}')

    @staticmethod
    def runtime_error(e: RuntimeException) -> None:
        Lox.had_runtime_error = True
        print(f'line: {e.token.line} at[{e.token.lexeme}]: {e.msg}')

    @staticmethod
    def run_file(path: str) -> None:
        with open(path, 'r') as f:
            source = f.read()
            Lox.run(source)
            if Lox.had_error:
                sys.exit(65)
            if Lox.had_runtime_error:
                sys.exit(66)

    @staticmethod
    def run(source: str) -> None:
        from interpreter.parser import Parser
        from interpreter.scanner import Scanner
        from interpreter.utils.ast_printer import AstPrinter
        from interpreter.interpreter_ import Interpreter

        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        stmts = parser.parse()
        if Lox.had_error:
            return
        # print(AstPrinter().build(expr))
        Interpreter().interpret(stmts)
