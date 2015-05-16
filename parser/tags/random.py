import os
import logging
from parser import schema, weighted_choice
from parser.tags import Tag


class Random(Tag):
    def __init__(self, saml, element):
        """
        Initialize a new Random Tag instance
        :param saml: The parent SAML instance
        :type  saml: Saml

        :param element: The XML Element object
        :type  element: etree._Element
        """
        super().__init__(saml, element)
        self._log = logging.getLogger('saml.parser.tags.random')

        # Define our schema
        with open(os.path.join(self.saml.script_path, 'schemas', 'tags', 'random.rng')) as file:
            self.schema = schema(file.read())

        self._responses = []
        self._element_to_dict()

    def _element_to_dict(self):
        """
        Generates a dictionary of responses from a <random> element
        """
        for child in self._element:
            self._log.debug('Appending response with weight {weight}: {response}'.format(weight=1, response=child.text))
            self._responses.append((child.text, 1))

    def __str__(self):
        return weighted_choice(self._responses)
