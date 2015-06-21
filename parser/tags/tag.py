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
