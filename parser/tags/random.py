import os
import logging
import random
from parser import schema
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

        self._responses = {}

    def _element_to_dict(self):
        """
        Generates a dictionary of responses from a <random> element
        """
        for child in self._element:
            self._responses[child.text] = 1

    @staticmethod
    def weighted_choice(choices):
        """
        Provides a weighted version of random.choice
        :param choices: A dictionary of choices, with the choice as the key and weight the value
        :type  choices: dict of (str, int)
        """
        total = sum(weight for choice, weight in choices)
        rand = random.uniform(0, total)
        most = 0

        for choice, weight in choices:
            if most + weight > rand:
                return choice
            most += weight

    def __str__(self):
        return self.weighted_choice(self._responses)