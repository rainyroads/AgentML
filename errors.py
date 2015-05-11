class SamlError(Exception):
    pass


class UserNotDefinedError(SamlError):
    pass


class VarNotDefinedError(SamlError):
    pass


class InvalidVarTypeError(SamlError):
    pass