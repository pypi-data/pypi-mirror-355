class CitycomError(Exception):
    """Exception raised for errors in the citycom API.

    Attributes:
        code -- input salary which caused the error.
        error -- description of the error
    """

    def __init__(self, code, error):
        self.code = code
        self.error = error
        super().__init__(f"(Code {self.code}): {self.error}")


class LoginError(CitycomError):
    """Exception raised for errors in the citycom Login.

    Attributes:
        code -- input salary which caused the error.
        error -- description of the error
    """

    def __init__(self, code, error):
        CitycomError.__init__(self, code, error)
