from __future__ import annotations
from interpreter.error import RuntimeException
from interpreter.token_ import Token


class Env:
    value_map: dict[str, object]
    # 外层作用域
    parent: Env

    def __init__(self, parent=None):
        self.value_map = {}
        self.parent = parent

    def define(self, k: str, v: object) -> None:
        self.value_map[k] = v

    def get(self, k: Token) -> object:
        if k.lexeme in self.value_map.keys():
            return self.value_map[k.lexeme]
        if self.parent is not None:
            return self.parent.get(k)
        raise RuntimeException(k, f"undefined variable '{k.lexeme}'")

    def assign(self, k: Token, v: object) -> None:
        if k.lexeme in self.value_map.keys():
            self.value_map[k.lexeme] = v
            return
        if self.parent is not None:
            self.parent.assign(k, v)
            return

        raise RuntimeException(k, f"undefined variable '{k.lexeme}'")

    def get_at(self, distance: int, name: str) -> object:
        target = self._ancestor(distance)
        return target.value_map[name]

    def assign_at(self, distance: int, name: Token, value: object) -> None:
        target = self._ancestor(distance)
        target.value_map[name.lexeme] = value

    def _ancestor(self, distance: int) -> Env:
        env = self
        for i in range(0, distance):
            env = env.parent
        return env
