class IncorrectDtype(Exception):
    def __init__(self,message):
        super().__init__(message)

class ModelHpMismatch(Exception):
    def __init__(self,message):
        super().__init__(message)

class DebugError(Exception):
    def __init__(self,message):
        super().__init__(message)

class ModelNotFound(Exception):
    def __init__(self,message):
        super().__init__(message)

class Experiment(Exception):
    def __init__(self,message):
        super().__init__(message)

class UnusableModule(Exception):
    def __init__(self,message):
        super().__init__(message)