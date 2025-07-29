from sys import stderr

class EmptyResponse(BaseException):
    
    def __init__(self, msg) -> None:
        print(msg, file=stderr)

class InvalidOperation(BaseException):
    
    def __init__(self, msg) -> None:
        print(msg, file=stderr)
        print(msg, file=stderr)

class TimeOut(BaseException):
    
    def __init__(self, msg) -> None:
        print(msg, file=stderr)


class GenericError(BaseException):
    
    def __init__(self, msg) -> None:
        print(msg, file=stderr)
