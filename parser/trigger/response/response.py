import os
import logging
from parser import Element
from parser.common import schema


class Response(Element):
    def __init__(self, trigger, element, file_path):
        self.trigger = trigger
        self._response = ()

        with open(os.path.join(self.trigger.saml.script_path, 'schemas', 'tags', 'star.rng')) as file:
            self.schema = schema(file.read())

        self._log = logging.getLogger('saml.parser.trigger.response')
        super().__init__(trigger.saml, element, file_path)

    def _parse(self):
        # If the response element has no tags, just store the raw text as the only response
        if not len(self._element):
            self._response = (self._element.text,)
            self._log.info('Assigning text only response')
            return

        self._response = tuple(self.saml.parse_tags(self._element))

    def __str__(self):
        self._log.debug('Converting Response object to string format')
        return ''.join(map(str, self._response)).strip()

