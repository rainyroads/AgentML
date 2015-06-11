import logging
from abc import ABCMeta, abstractmethod
from parser import Element, attribute, int_attribute
from parser.trigger.response import Response
from errors import VarNotDefinedError


class BaseCondition(metaclass=ABCMeta):
    """
    SAML Base Condition class
    """
    def __init__(self, saml, element, **kwargs):
        """
        Initialize a new Base Condition instance
        :param saml: The parent SAML instance
        :type  saml: Saml

        :param element: The XML Element object
        :type  element: etree._Element

        :param kwargs: Default attributes
        """
        self.saml = saml
        self._element = element

        # Containers and default attributes
        self._comparisons = []
        self._else = NotImplemented
        self.type = kwargs['type'] if 'type' in kwargs else 'user_var'

    def evaluate(self, user):
        """
        Evaluate the conditional statement and return its contents if a successful evaluation takes place
        :param user: The active user object
        :type  user: saml.User or None

        :return: A list of (response, weight) tuples, or an empty tuple if the evaluation fails
        :rtype : list of tuple or list
        """
        for comparison in self._comparisons:
            key_type, key, operator, value, items = comparison
            self._log.debug('Evaluating conditional statement: {key} {operator} {value}'
                            .format(key=key, operator=operator, value=value))

            # Get the value of our key type
            key_value = None
            try:
                if key_type == 'user_var':
                    key_value = user.get_var(key)
                elif key_type == 'global_var':
                    key_value = self.saml.get_var(key)
                elif key_type == 'topic':
                    key_value = user.topic
                elif key_type == 'user':
                    key_value = user.id
            except VarNotDefinedError:
                key_value = None

            # Atomic comparisons
            if operator is NotImplemented and key_value:
                return items

            if (operator == 'is') and (key_value == value):
                return items

            if (operator == 'is_not') and (key_value != value):
                return items

            # All remaining operators are numeric based, so key_value must contain a valid integer or float
            try:
                key_value = float(key_value)
                value = float(value)
            except (ValueError, TypeError):
                continue

            # Numeric comparisons
            if (operator == 'gt') and (key_value > value):
                return items

            if (operator == 'gte') and (key_value >= value):
                return items

            if (operator == 'lt') and (key_value < value):
                return items

            if (operator == 'lte') and (key_value <= value):
                return items

        if self._else is not NotImplemented:
            return self._else

        return ()

    @abstractmethod
    def get_contents(self, element):
        """
        Retrieve the contents of an element
        :param element: The XML Element object
        :type  element: etree._Element

        :return: A list of text and/or XML elements
        :rtype : list of etree._Element or str
        """
        pass

    def _parse(self):
        """
        Loop through all child elements and execute any available parse methods for them
        """
        self.type = attribute(self._element, 'type') or self.type

        for child in self._element:
            method_name = '_parse_{0}'.format(str(child.tag))  # TODO: This is a hack, skip comment objects here

            if hasattr(self, method_name):
                parse = getattr(self, method_name)
                parse(child)

    def _parse_if(self, element):
        """
        Parse the if statement
        :param element: The XML Element object
        :type  element: etree._Element
        """
        # Get the key
        name = attribute(element, 'name')

        # Get the comparison operator and its value (if implemented)
        operator = NotImplemented
        value = NotImplemented
        for o in ['is', 'is_not', 'gt', 'gte', 'lt', 'lte']:
            if o in element.attrib:
                operator = o
                value = element.attrib[operator]
                break

        # Get the contents of the element in tuple form and append our if statement
        contents = tuple(self.get_contents(element))
        self._comparisons.append((self.type, name, operator, value, contents))

    def _parse_elif(self, element):
        """
        Parse an elif statement
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self._parse_if(element)

    def _parse_else(self, element):
        """
        Parse the else statement
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self._else = self.get_contents(element)


class Condition(Element, BaseCondition):
    """
    SAML Condition object
    """
    def __init__(self, trigger, element, file_path):
        """
        Initialize a new Condition instance
        :param trigger: The Trigger instance
        :type  trigger: Trigger

        :param element: The XML Element object
        :type  element: etree._Element

        :param file_path: The absolute path to the SAML file
        :type  file_path: str
        """
        self.trigger = trigger
        BaseCondition.__init__(self, trigger.saml, element)
        Element.__init__(self, trigger.saml, element, file_path)
        self._log = logging.getLogger('saml.parser.trigger.condition')

    def get_contents(self, element):
        """
        Retrieve the contents of an element
        :param element: The XML Element object
        :type  element: etree._Element

        :return: A list of responses
        :rtype : list of Response
        """
        return [(Response(self.trigger, child, self.file_path), int_attribute(child, 'weight', 1))
                for child in element if child.tag == 'response']
