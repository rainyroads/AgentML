class AgentMLError(Exception):
    pass


class AgentMLSyntaxError(AgentMLError):
    pass


class UserNotDefinedError(AgentMLError):
    pass


class VarNotDefinedError(AgentMLError):
    pass


class InvalidVarTypeError(AgentMLError):
    pass


class NoTagParserError(AgentMLError):
    pass


###############################
# Parser Blocking Errors
###############################
# These are errors that are used to halt iteration over Triggers or Responses

class ParserBlockingError(AgentMLError):
    pass


class LimitError(ParserBlockingError):
    pass


class ChanceError(ParserBlockingError):
    pass
