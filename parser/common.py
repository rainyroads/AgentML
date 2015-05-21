import re
import random
from lxml import etree


def schema(relaxng):
    """
    Parse a RelaxNG schema document and return an etree instance of it
    :param relaxng: The RelaxNG schema as a string
    :type  relaxng: str

    :return: LXML etree RelaxNG instance
    :rtype : etree.RelaxNG
    """
    tree = etree.fromstring(relaxng)
    return etree.RelaxNG(tree)

def weighted_choice(choices):
    """
    Provides a weighted version of random.choice
    :param choices: A dictionary of choices, with the choice as the key and weight the value
    :type  choices: list of tuple of (str, int)
    """
    total = sum(weight for choice, weight in choices)
    rand = random.uniform(0, total)
    most = 0

    for choice, weight in choices:
        if most + weight > rand:
            return choice
        most += weight

def normalize(string, pattern=False):
    """
    Normalize input for comparison with other input
    :param string: The string to normalize
    :type  string: str

    :param pattern: Allow wildcard symbols for triggers
    :type  pattern: bool

    :rtype: str
    """
    regex = re.compile(r'([^\s\w\*#])+') if pattern else re.compile(r'([^\s\w]|_)+')

    if not isinstance(string, str):
        return ''

    return regex.sub('', string.strip().casefold())

def attribute(element, attribute, default=None):
    """
    Returns the value of an attribute, or a default if it's not defined
    :param element: The XML Element object
    :type  element: etree._Element

    :param attribute: The name of the attribute to evaluate
    :type  attribute: str

    :param default: The default value to return if the attribute is not defined
    """
    attribute_value = element.get(attribute)

    return attribute_value if attribute_value is not None else default

def bool_attribute(element, attribute, default=True):
    """
    Returns the bool value of an attribute, or a default if it's not defined
    :param element: The XML Element object
    :type  element: etree._Element

    :param attribute: The name of the attribute to evaluate
    :type  attribute: str

    :param default: The default boolean to return if the attribute is not defined
    :type  default: bool

    :rtype: bool
    """
    attribute_value = element.get(attribute)

    if attribute_value:
        return True if (attribute_value == 'true') else False

    return default

def int_attribute(element, attribute, default=0):
    """
    Returns the int value of an attribute, or a default if it's not defined
    :param element: The XML Element object
    :type  element: etree._Element

    :param attribute: The name of the attribute to evaluate
    :type  attribute: str

    :param default: The default value to return if the attribute is not defined
    :type  default: int

    :rtype: int
    """
    attribute_value = element.get(attribute)

    if attribute_value:
        try:
            return int(attribute_value)
        except (TypeError, ValueError):
            return default

    return default
