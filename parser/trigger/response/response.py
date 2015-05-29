import os
import time
import logging
from parser import Element
from parser.common import schema, normalize, attribute


class Response(Element):
    def __init__(self, trigger, element, file_path):
        self.trigger = trigger
        self._response = ()

        # Assignment attributes
        self.topic = False
        self.mood = False
        self.global_limit = False
        self.user_limit = False
        self.chance = 100

        with open(os.path.join(self.trigger.saml.script_path, 'schemas', 'tags', 'star.rng')) as file:
            self.schema = schema(file.read())

        self._log = logging.getLogger('saml.parser.trigger.response')
        super().__init__(trigger.saml, element, file_path)

    def apply_reactions(self, user):
        # User attributes
        if self.topic is not False:
            self._log.debug('Setting User Topic to: {0}'.format(self.topic))
            user.topic = self.topic

        if self.global_limit is not False:
            self._log.debug('Setting Global Limit to {0} seconds'.format(self.global_limit))
            pass  # TODO

        if self.user_limit is not False:
            self._log.debug('Setting User Limit to {0} seconds'.format(self.user_limit))
            user._limits[id(self)] = ((time.time() + self.user_limit), False)

        # saml.mood = self.mood

    def _parse(self):
        # Assign the message as the element itself, or a sub message element if one has been defined
        template = self._element.find('template')
        if template:
            for child in self._element:
                method_name = '_parse_' + child.tag

                if hasattr(self, method_name):
                    parse = getattr(self, method_name)
                    parse(child)
        else:
            template = self._element

        # If the response element has no tags, just store the raw text as the only response
        if not len(template):
            self._response = (template.text,)
            self._log.info('Assigning text only response')
            return

        self._response = tuple(self.saml.parse_tags(template, self.trigger))

    def __str__(self):
        self._log.debug('Converting Response object to string format')
        return ''.join(map(str, self._response)).strip()

