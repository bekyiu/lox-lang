class ParseError(Exception):
    msg: str

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg
