from interpreter.token_ import Token


class ParseException(Exception):
    msg: str

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg


class RuntimeException(Exception):
    token: Token
    msg: str

    def __init__(self, token, msg):
        super().__init__(msg)
        self.token = token
        self.msg = msg

    def __repr__(self):
        return self.msg + str(self.token)


class ReturnException(Exception):
    value: object

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'return exception, value: {self.value}'


class BreakException(Exception):

    def __repr__(self):
        return 'break exception'
