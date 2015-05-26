import os
import logging
from parser import Element
from parser.common import schema


class Response(Element):
    def __init__(self, trigger, element, file_path):
        self.trigger = trigger
        self._response = ()

        # Assignment attributes
        self.topic = None
        self.mood = None

        with open(os.path.join(self.trigger.saml.script_path, 'schemas', 'tags', 'star.rng')) as file:
            self.schema = schema(file.read())

        self._log = logging.getLogger('saml.parser.trigger.response')
        super().__init__(trigger.saml, element, file_path)

    def apply_reactions(self, user):
        self._log.debug('Setting topic to: ' + str(self.topic))
        user.topic = self.topic
        # saml.mood = self.mood

    def _parse(self):
        # Assign the message as the element itself, or a sub message element if one has been defined
        message = self._element.find('message')
        if message:
            for child in self._element:
                if child.tag == 'topic':
                    self.topic = child.text
                    continue
        else:
            message = self._element

        # If the response element has no tags, just store the raw text as the only response
        if not len(message):
            self._response = (message.text,)
            self._log.info('Assigning text only response')
            return

        self._response = tuple(self.saml.parse_tags(message, self.trigger))

    def __str__(self):
        self._log.debug('Converting Response object to string format')
        return ''.join(map(str, self._response)).strip()

