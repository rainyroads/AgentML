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


def normalize(string, pattern=False, preserve_case=False):
    """
    Normalize input for comparison with other input
    :param string: The string to normalize
    :type  string: str

    :param pattern: Allow wildcard symbols for triggers
    :type  pattern: bool

    :param preserve_case: Normalize the message without casefolding
    :type  preserve_case: bool

    :rtype: str
    """
    regex = re.compile(r'([^\s\w\(\)\[\]\|\*#])+') if pattern else re.compile(r'([^\s\w]|_)+')

    if not isinstance(string, str):
        return ''

    # Case folding is not supported in Python2
    try:
        string = string.strip() if preserve_case else string.strip().casefold()
    except AttributeError:
        string = string.strip() if preserve_case else string.strip().lower()

    return regex.sub('', string)


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
        return attribute_value == 'true'

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


def element(element, name, default=None):
    """
    Returns the value of an element, or a default if it's not defined
    :param element: The XML Element object
    :type  element: etree._Element

    :param name: The name of the element to evaluate
    :type  name: str

    :param default: The default value to return if the element is not defined
    """
    element_value = element.find(name)

    return element_value.text if element_value is not None else default


def bool_element(element, name, default=True):
    """
    Returns the bool value of an element, or a default if it's not defined
    :param element: The XML Element object
    :type  element: etree._Element

    :param name: The name of the element to evaluate
    :type  name: str

    :param default: The default value to return if the element is not defined
    :type  default: bool
    """
    element_value = element.find(name)

    if element_value is not None:
        return element_value.text == 'true'

    return default


def int_element(element, name, default=0):
    """
    Returns the int value of an element, or a default if it's not defined
    :param element: The XML Element object
    :type  element: etree._Element

    :param name: The name of the element to evaluate
    :type  name: str

    :param default: The default value to return if the element is not defined
    :type  default: int

    :rtype: int
    """
    element_value = element.find(name)

    if element_value is not None:
        try:
            return int(element_value.text)
        except (TypeError, ValueError):
            return default

    return default


def newlines_to_spaces(text):
    """
    Strips newlines and any spacing surrounding the newlines and replaces them with a single space
    :param text: The text to parse
    :type  text: str
    """
    newline_pattern = re.compile('\s*\n\s*')
    return newline_pattern.sub(' ', text)
