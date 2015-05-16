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

def normalize(self, string):
    """
    Normalize input for comparison with other input
    :param string: The string to normalize
    :type  string: str

    :rtype: str
    """
    if not isinstance(string, str):
        self._log.warn('Attempted to normalize a non-string')
        return ''

    return re.sub(r'([^\s\w]|_)+', '', string.strip().casefold())