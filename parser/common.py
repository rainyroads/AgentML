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
