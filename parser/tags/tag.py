class Tag:
    def __init__(self, saml, element):
        self.saml = saml
        self._element = element

        # TODO: Optional schema validation
        self.schema = NotImplemented