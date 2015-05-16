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