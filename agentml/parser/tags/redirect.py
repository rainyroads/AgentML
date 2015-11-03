import os
import logging
from agentml.common import schema, attribute
from agentml.parser.tags import Tag


class Redirect(Tag):
    def __init__(self, trigger, element):
        """
        Initialize a new Random Tag instance
        :param trigger: The executing Trigger instance
        :type  trigger: parser.trigger.Trigger

        :param element: The XML Element object
        :type  element: etree._Element
        """
        super(Redirect, self).__init__(trigger, element)
        self._log = logging.getLogger('agentml.parser.tags.redirect')

        # Define our schema
        with open(os.path.join(self.trigger.agentml.script_path, 'schemas', 'tags', 'redirect.rng')) as file:
            self.schema = schema(file.read())

    def value(self):
        """
        Return the value of the redirect response
        """
        user = self.trigger.agentml.request_log.most_recent().user
        groups = self.trigger.agentml.request_log.most_recent().groups

        # Does the redirect statement have tags to parse?
        if len(self._element):
            message = ''.join(map(str, self.trigger.agentml.parse_tags(self._element, self.trigger)))
        else:
            message = self._element.text

        # Is there a default value defined?
        default = attribute(self._element, 'default', '')
        response = self.trigger.agentml.get_reply(user.id, message, groups)

        return response or default
