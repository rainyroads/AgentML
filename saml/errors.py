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


###############################
# Parser Blocking Errors
###############################
# These are errors that are used to halt iteration over Triggers or Responses

class ParserBlockingError(SamlError):
    pass


class LimitError(ParserBlockingError):
    pass


class ChanceError(ParserBlockingError):
    pass
