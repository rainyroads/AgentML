class SamlError(Exception):
    pass


class SamlSyntaxError(SamlError):
    pass


class UserNotDefinedError(SamlError):
    pass


class VarNotDefinedError(SamlError):
    pass


class InvalidVarTypeError(SamlError):
    pass


class NoTagParserError(SamlError):
    pass
