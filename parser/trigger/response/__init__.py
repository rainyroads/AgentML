import os
import time
import logging
from collections import Iterable
from common import schema, attribute, int_attribute
from parser import Element, Restrictable
from .container import ResponseContainer


class Response(Element, Restrictable):
    """
    SAML Response object
    """
    def __init__(self, trigger, element, file_path, **kwargs):
        """
        Initialize a new Response instance
        :param trigger: The Trigger instance
        :type  trigger: Trigger

        :param element: The XML Element object
        :type  element: etree._Element

        :param file_path: The absolute path to the SAML file
        :type  file_path: str

        :param kwargs: Default attributes
        """
        # Containers and default attributes
        self.priority = int_attribute(element, 'priority')
        self.trigger = trigger
        self._response = ()
        self.topic = False
        self.var = (None, None, None)

        # Parent __init__'s must be initialized BEFORE default attributes are assigned, but AFTER the above containers
        Restrictable.__init__(self)
        Element.__init__(self, trigger.saml, element, file_path)

        # Default attributes
        self.emotion = kwargs['emotion'] if 'emotion' in kwargs else None
        self.weight = kwargs['weight'] if 'weight' in kwargs else int_attribute(self._element, 'weight', 1)
        self.ulimit_blocking = False
        self.glimit_blocking = False
        self.chance_blocking = False

        with open(os.path.join(self.trigger.saml.script_path, 'schemas', 'tags', 'star.rng')) as file:
            self.schema = schema(file.read())

        self._log = logging.getLogger('saml.parser.trigger.response')

    def apply_reactions(self, user):
        """
        Set active topics and limits after a response has been triggered
        :param user: The user triggering the response
        :type  user: saml.User
        """
        # User attributes
        if self.topic is not False:
            self._log.info('Setting User Topic to: {topic}'.format(topic=self.topic))
            user.topic = self.topic

        if self.global_limit:
            self._log.info('Enforcing Global Response Limit of {num} seconds'.format(num=self.global_limit))
            pass  # TODO

        if self.user_limit:
            self._log.info('Enforcing User Response Limit of {num} seconds'.format(num=self.user_limit))
            user.set_limit(self, (time.time() + self.user_limit))

        if self.var[0]:
            var_type, var_name, var_value = self.var
            var_name  = ''.join(map(str, var_name)) if isinstance(var_name, Iterable) else var_name
            var_value = ''.join(map(str, var_value)) if isinstance(var_value, Iterable) else var_value

            # Set a user variable
            if var_type == 'user':
                self.trigger.user.set_var(var_name, var_value)

            # Set a global variable
            if var_type == 'global':
                self.trigger.saml.set_var(var_name, var_value)

        # saml.mood = self.mood

    def _parse(self):
        """
        Loop through all child elements and execute any available parse methods for them
        """
        # Find the template and parse any other defined tags
        template = self._element.find('template')
        for child in self._element:
            method_name = '_parse_' + child.tag

            if hasattr(self, method_name):
                parse = getattr(self, method_name)
                parse(child)

        # If the response element has no tags, just store the raw text as the only response
        if not len(template):
            self._response = (template.text,)
            self._log.info('Assigning text only response')
            return

        self._response = tuple(self.saml.parse_tags(template, self.trigger))

    def _parse_priority(self, element):
        """
        Parse and assign the priority for this response
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self._log.debug('Setting Trigger priority: {priority}'.format(priority=element.text))
        self.priority = int(element.text)

    def _parse_var(self, element):
        """
        Parse a variable assignment
        :param element: The XML Element object
        :type  element: etree._Element
        """
        syntax = 'attribute' if element.get('name') else 'element'

        var_type = attribute(element, 'type', 'user')
        if syntax == 'attribute':
            var_name  = attribute(element, 'name')
            var_value   = self.saml.parse_tags(element, self.trigger) if len(element) else element.text
        else:
            name_etree = element.find('name')
            var_name   = self.saml.parse_tags(name_etree, self.trigger) if len(name_etree) else name_etree.text

            value_etree = element.find('value')
            var_value = self.saml.parse_tags(value_etree, self.trigger) if len(value_etree) else value_etree.text

        self.var = (var_type, var_name, var_value)

    def __str__(self):
        self._log.debug('Converting Response object to string format')
        response = ''.join(map(str, self._response)).strip()

        self._log.debug('Resetting parent Trigger temporary containers')
        self.stars = {
            'normalized': (),
            'case_preserved': (),
            'raw': ()
        }
        self.trigger.user = None
        return response
