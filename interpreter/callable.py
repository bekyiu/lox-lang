import time
from abc import ABCMeta, abstractmethod

from interpreter.env import Env
from interpreter.error import ReturnException
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


# lox函数在python中的表示, 它会绑定一个名字存在环境中
class LoxFunction(Callable):
    declaration: Function
    closure_env: Env

    def __init__(self, declaration, env):
        self.declaration = declaration
        # 在创建当前这个函数的同时 保存这个函数所在的环境
        self.closure_env = env

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        # 每执行一个函数 都需要一个新的环境 来保存当前函数的局部变量
        env = Env(self.closure_env)
        for i, param in enumerate(self.declaration.params):
            arg = arguments[i]
            env.define(param.lexeme, arg)

        try:
            interpreter.execute_block(self.declaration.body, env)
        except ReturnException as e:
            return e.value

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
