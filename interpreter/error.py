from interpreter.token import Token


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

    def __repr__(self):
        return self.msg + str(self.token)
