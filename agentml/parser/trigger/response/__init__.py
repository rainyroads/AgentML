import os
import logging
from time import time
from collections import Iterable
from agentml.common import schema, attribute, int_attribute, int_element
from agentml.parser import Element, Restrictable
from .container import ResponseContainer


class Response(Element, Restrictable):
    """
    AgentML Response object
    """
    def __init__(self, trigger, element, file_path, **kwargs):
        """
        Initialize a new Response instance
        :param trigger: The Trigger instance
        :type  trigger: Trigger

        :param element: The XML Element object
        :type  element: etree._Element

        :param file_path: The absolute path to the AgentML file
        :type  file_path: str

        :param kwargs: Default attributes
        """
        self.priority = int_attribute(element, 'priority')
        self.weight = int_attribute(element, 'weight', 1)
        self.trigger = trigger

        # If the redirect attribute is True, the response will contain a template used to request a different response,
        # otherwise it contains a template for the response message
        self._response = ()
        self.redirect = False

        # What the topic should be *changed* to after this response is sent. False = No change
        self.topic = False

        # Variable to set. Format is (type, name, value)
        self.var = (None, None, None)

        # Wildcard containers
        self.stars = {
            'normalized': (),
            'case_preserved': (),
            'raw': ()
        }

        Restrictable.__init__(self)
        Element.__init__(self, trigger.agentml, element, file_path)

        # Blocking attributes
        self.ulimit_blocking = False
        self.glimit_blocking = False
        self.chance_blocking = False

        self._log = logging.getLogger('agentml.parser.trigger.response')

    def get(self):
        """
        Parse a response into string format and clear out its temporary containers
        :return: The parsed response message
        :rtype : str
        """
        self._log.debug('Converting Response object to string format')
        response = ''.join(map(str, self._response)).strip()

        self._log.debug('Resetting parent Trigger temporary containers')
        self.stars = {
            'normalized': (),
            'case_preserved': (),
            'raw': ()
        }
        user = self.trigger.user
        self.trigger.user = None

        if self.redirect:
            self._log.info('Redirecting response to: {msg}'.format(msg=response))
            groups = self.agentml.request_log.most_recent().groups
            response = self.agentml.get_reply(user.id, response, groups)
            if not response:
                self._log.info('Failed to retrieve a valid response when redirecting')
                return ''

        return response

    def apply_reactions(self, user):
        """
        Set active topics and limits after a response has been triggered
        :param user: The user triggering the response
        :type  user: agentml.User
        """
        # User attributes
        if self.topic is not False:
            self._log.info('Setting User Topic to: {topic}'.format(topic=self.topic))
            user.topic = self.topic

        if self.global_limit:
            self._log.info('Enforcing Global Response Limit of {num} seconds'.format(num=self.global_limit))
            self.agentml.set_limit(self, (time() + self.global_limit), self.glimit_blocking)

        if self.user_limit:
            self._log.info('Enforcing User Response Limit of {num} seconds'.format(num=self.user_limit))
            user.set_limit(self, (time() + self.user_limit))

        if self.var[0]:
            var_type, var_name, var_value = self.var
            var_name  = ''.join(map(str, var_name)) if isinstance(var_name, Iterable) else var_name
            var_value = ''.join(map(str, var_value)) if isinstance(var_value, Iterable) else var_value

            # Set a user variable
            if var_type == 'user':
                self.trigger.user.set_var(var_name, var_value)

            # Set a global variable
            if var_type == 'global':
                self.trigger.agentml.set_var(var_name, var_value)

    def _parse(self):
        """
        Loop through all child elements and execute any available parse methods for them
        """
        def parse_template(element):
            # If the response element has no tags, just store the raw text as the only response
            if not len(element):
                self._response = (element.text,)
                self._log.info('Assigning text only response')
                return

            # Otherwise, parse the tags now
            self._response = tuple(self.agentml.parse_tags(element, self.trigger))

        # Is this a shorthand template?
        if self._element.tag == 'template':
            return parse_template(self._element)

        # Is this a redirect?
        redirect = self._element if self._element.tag == 'redirect' else self._element.find('redirect')
        if redirect is not None:
            self._log.info('Parsing response as a redirect')
            self.redirect = True
            return parse_template(redirect)

        # Find the template and parse any other defined tags
        template = self._element.find('template')
        parse_template(template)
        for child in self._element:
            method_name = '_parse_' + child.tag

            if hasattr(self, method_name):
                parse = getattr(self, method_name)
                parse(child)

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
            var_value   = self.agentml.parse_tags(element, self.trigger) if len(element) else element.text
        else:
            name_etree = element.find('name')
            var_name   = self.agentml.parse_tags(name_etree, self.trigger) if len(name_etree) else name_etree.text

            value_etree = element.find('value')
            var_value = self.agentml.parse_tags(value_etree, self.trigger) if len(value_etree) else value_etree.text

        self.var = (var_type, var_name, var_value)

    def __str__(self):
        return self.get()
