import os
import logging
from common import schema, int_attribute, weighted_choice
from parser.tags import Tag


class Random(Tag):
    def __init__(self, trigger, element):
        """
        Initialize a new Random Tag instance
        :param trigger: The Trigger instance
        :type  trigger: Trigger

        :param element: The XML Element object
        :type  element: etree._Element
        """
        super().__init__(trigger, element)
        self._log = logging.getLogger('saml.parser.tags.random')

        # Define our schema
        with open(os.path.join(self.trigger.saml.script_path, 'schemas', 'tags', 'random.rng')) as file:
            self.schema = schema(file.read())

        self._responses = ()
        self._parse()

    def _parse(self):
        """
        Generates a dictionary of responses from a <random> element
        """
        responses = []
        for child in self._element:
            weight = int_attribute(child, 'weight', 1)
            self._log.debug('Parsing random entry with weight {weight}: {entry}'
                            .format(weight=weight, entry=child.text))

            # If the random element doesn't contain any tags, just store the text and return
            if not len(child):
                responses.append((child.text, weight))
                continue

            # Otherwise, parse all the available tags
            responses.append((tuple(self.trigger.saml.parse_tags(child, self.trigger)), weight))
        self._responses = tuple(responses)

    def value(self):
        """
        Fetch a random weighted choice
        """
        choice = weighted_choice(self._responses)

        # If the choice is a tuple, join the elements into a single mapped string
        if isinstance(choice, tuple):
            return ''.join(map(str, choice)).strip()

        # Otherwise, return the choice itself as a string
        return str(choice)
