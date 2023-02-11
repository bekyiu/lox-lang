import time
from abc import ABCMeta, abstractmethod
from interpreter.interpreter_ import Interpreter


class Callable(metaclass=ABCMeta):
    @abstractmethod
    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        pass

    # 形参个数
    @abstractmethod
    def arity(self) -> int:
        pass


# 内置函数
class Clock(Callable):

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        return time.time()

    def arity(self) -> int:
        return 0

    def __repr__(self):
        return '<native fn>'
