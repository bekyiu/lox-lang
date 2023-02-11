import time
from abc import ABCMeta, abstractmethod

from interpreter.env import Env
from interpreter.interpreter_ import Interpreter
from interpreter.stmt import Function


class Callable(metaclass=ABCMeta):
    @abstractmethod
    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        pass

    # 形参个数
    @abstractmethod
    def arity(self) -> int:
        pass


class LoxFunction(Callable):
    declaration: Function

    def __init__(self, declaration):
        self.declaration = declaration

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        env = Env(interpreter.outermost)
        for i, param in enumerate(self.declaration.params):
            arg = arguments[i]
            env.define(param.lexeme, arg)

        interpreter.execute_block(self.declaration.body, env)
        return None

    def arity(self) -> int:
        return len(self.declaration.params)

    def __repr__(self):
        return f'<fn {self.declaration.name.lexeme}>'


# 内置函数
class Clock(Callable):

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        return time.time()

    def arity(self) -> int:
        return 0

    def __repr__(self):
        return '<native fn>'
