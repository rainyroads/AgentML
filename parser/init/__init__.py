from lxml import etree
from parser import Element, normalize, attribute


class Init(Element):
    """
    SAML Initialization
    """
    def __init__(self, saml, element, file_path, **kwargs):
        """
        Initialize a new Init instance
        """
        super().__init__(saml, element, file_path)

    def _parse_substitutions(self, element):
        """
        Parse word substitutions
        :param element: The XML Element object
        :type  element: etree._Element
        """
        subs = element.findall('sub')

        for sub in subs:
            self.saml.set_substitution(attribute(sub, 'word'), sub.text)
