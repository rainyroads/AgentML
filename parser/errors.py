from errors import SamlError


class SamlSyntaxError(SamlError):
    pass


class NoTagParserError(SamlError):
    pass