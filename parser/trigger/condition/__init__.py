import logging
from abc import ABCMeta, abstractmethod
from common import attribute, int_attribute
from parser import Element
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
        self.statements = []
        self._else = None

        self.type = kwargs['type'] if 'type' in kwargs else attribute(self._element, 'type', 'user_var')
        self._log = logging.getLogger('saml.parser.trigger.condition')

    def evaluate(self, user):
        """
        Evaluate the conditional statement and return its contents if a successful evaluation takes place
        :param user: The active user object
        :type  user: saml.User or None

        :return: True if the condition evaluates successfully, otherwise False
        :rtype : bool
        """
        for statement in self.statements:
            evaluated = statement.evaluate(self.saml, user)
            if evaluated:
                return evaluated

        return self._else or False

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
        cond_type = attribute(element, 'type', self.type)

        # Get the comparison operator and its value (if implemented)
        operator = None
        value = None
        for o in ConditionStatement.operators:
            if o in element.attrib:
                operator = o
                value = element.attrib[operator]
                break

        # Get the contents of the element in tuple form and append our if statement
        contents = tuple(self.get_contents(element))
        self.statements.append(ConditionStatement(cond_type, operator, contents, value, name))

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
        return [Response(self.trigger, child, self.file_path) for child in element if child.tag == 'response']

class ConditionStatement:
    # Condition types
    USER_VAR = 'user_var'
    GLOBAL_VAR = 'global_var'
    TOPIC = 'topic'
    USER = 'user'

    types = [USER_VAR, GLOBAL_VAR, TOPIC, USER]

    # Condition operators
    IS = 'is'
    IS_NOT = 'is_not'
    GREATER_THAN = 'gt'
    GREATER_THAN_OR_EQUAL = 'gte'
    LESS_THAN = 'lt'
    LESS_THAN_OR_EQUAL = 'lte'

    operators = [IS, IS_NOT, GREATER_THAN, GREATER_THAN_OR_EQUAL, LESS_THAN, LESS_THAN_OR_EQUAL]

    def __init__(self, cond_type, operator, contents, value=None, name=None):
        """
        Initialize a new Condition Statement object
        :param cond_type: The type of the condition statement
        :type  cond_type: str

        :param operator: The operator of the condition statement
        :type  operator: str

        :param contents: The contents of the condition statement
        :type  contents: tuple

        :param value: The value of the condition statement
        :type  value: str, int, float or None

        :param name: The name of the variable if the condition type is USER_VAR or GLOBAL_VAR
        :type  name: str
        """
        self.type = cond_type
        self.operator = operator
        self.contents = contents
        self.value = value
        self.name = name
        self._log = logging.getLogger('saml.parser.trigger.condition.statement')

    def evaluate(self, saml, user=None):
        """
        Evaluate the conditional statement and return its contents if a successful evaluation takes place
        :param user: The active user object
        :type  user: saml.User or None
        
        :param saml: The active SAML instance
        :type  saml: Saml

        :return: Condition contents if the condition evaluates successfully, otherwise False
        :rtype : tuple or bool
        """
        self._log.debug('Evaluating conditional statement: {statement}'
                        .format(statement=' '.join(filter(None, [self.type, self.name, self.operator, self.value]))))

        # Get the value of our key type
        key_value = None
        try:
            if self.type == self.USER_VAR:
                key_value = user.get_var(self.name)
            elif self.type == self.GLOBAL_VAR:
                key_value = saml.get_var(self.name)
            elif self.type == self.TOPIC:
                key_value = user.topic
            elif self.type == self.USER:
                key_value = user.id
        except VarNotDefinedError:
            key_value = None

        # Atomic comparisons
        if self.operator is NotImplemented and key_value:
            return self.contents

        if (self.operator == self.IS) and (key_value == self.value):
            return self.contents

        if (self.operator == self.IS_NOT) and (key_value != self.value):
            return self.contents

        # All remaining self.operators are numeric based, so key_value must contain a valid integer or float
        try:
            key_value = float(key_value)
            value = float(self.value)
        except (ValueError, TypeError):
            return False

        # Numeric comparisons
        if (self.operator == self.GREATER_THAN) and (key_value > value):
            return self.contents

        if (self.operator == self.GREATER_THAN_OR_EQUAL) and (key_value >= value):
            return self.contents

        if (self.operator == self.LESS_THAN) and (key_value < value):
            return self.contents

        if (self.operator == self.LESS_THAN_OR_EQUAL) and (key_value <= value):
            return self.contents

        return False
