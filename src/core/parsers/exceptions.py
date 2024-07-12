
class ParserException(Exception):
    def __init__(self, message):
        super(ParserException, self).__init__(message)
        self.message = message
