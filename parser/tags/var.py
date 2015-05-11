import os
import logging
from parser import schema
from parser.tags import Tag
from errors import SamlError


class Var(Tag):
    def __init__(self, saml, element):
        """
        Initialize a new Random Tag instance
        :param saml: The parent SAML instance
        :type  saml: Saml

        :param element: The XML Element object
        :type  element: etree._Element
        """
        super().__init__(saml, element)
        self._log = logging.getLogger('saml.parser.tags.var')

        # Define our schema
        with open(os.path.join(self.saml.script_path, 'schemas', 'tags', 'var.rng')) as file:
            self.schema = schema(file.read())

    def __str__(self):
        try:
            return self.saml.get_var(self._element.text)
        except SamlError:
            return ''