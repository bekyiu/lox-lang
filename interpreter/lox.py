import sys


class Lox:
    had_error: bool = False

    @staticmethod
    def start() -> None:
        Lox.run_file()

    @staticmethod
    def log(*args, sep: str = ' ', end: str = '\n'):
        print(*args, sep=sep, end=end)

    @staticmethod
    def error(line: int, where: str, message: str) -> None:
        Lox.had_error = True
        Lox.log(f'line: {line}, error[{where}]: {message}')

    @staticmethod
    def run_file(path: str) -> None:
        with open(path, 'r') as f:
            source = f.read()
            Lox.run(source)
            if Lox.had_error:
                sys.exit(65)

    @staticmethod
    def run(source: str) -> None:
        Lox.log(source)
