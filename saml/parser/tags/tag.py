import logging
from abc import ABCMeta, abstractmethod


class Tag(metaclass=ABCMeta):
    """
    Tag base class
    """
    def __init__(self, trigger, element):
        """
        Initialize a new Tag instance
        :param trigger: The executing Trigger instance
        :type  trigger: parser.trigger.Trigger

        :param element: The XML Element object
        :type  element: etree._Element
        """
        self.trigger = trigger
        self._element = element
        self._schema = None
        self._log = logging.getLogger('saml.parser.tags')
        self._parse()

    def _parse(self):
        """
        Loop through all child elements and execute any available parse methods for them
        """
        for child in self._element:
            method_name = '_parse_{0}'.format(str(child.tag))  # TODO: This is a hack, skip comment objects here

            if hasattr(self, method_name):
                parse = getattr(self, method_name)
                parse(child)

    @property
    def schema(self):
        return self._schema

    @schema.setter
    def schema(self, schema):
        self._log.debug('Validating {tag} Tag schema'.format(tag=self._element.tag))
        schema.assertValid(self._element)
        self._schema = schema

    @abstractmethod
    def value(self):
        """
        Parse and return the value of the tag
        :rtype: str
        """
        pass

    def __str__(self):
        return self.value()
