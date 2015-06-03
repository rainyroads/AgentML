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
# Trigger Blocking Errors
###############################
# These are errors that are used to halt iteration over Triggers. One example of this include a global or user limit
# being triggered. When one of these errors is raised, Trigger matching is aborted and a None response will be returned

class TriggerBlockingError(SamlError):
    pass


class LimitError(TriggerBlockingError):
    pass


class ChanceError(TriggerBlockingError):
    pass
