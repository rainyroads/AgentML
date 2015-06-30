from lxml import etree
from agentml.common import attribute
from agentml.parser import Element


class Init(Element):
    """
    AgentML Initialization
    """
    def __init__(self, agentml, element, file_path, **kwargs):
        """
        Initialize a new Init instance
        """
        super().__init__(agentml, element, file_path)

    def _parse_substitutions(self, element):
        """
        Parse word substitutions
        :param element: The XML Element object
        :type  element: etree._Element
        """
        subs = element.findall('sub')

        for sub in subs:
            self.agentml.set_substitution(attribute(sub, 'word'), sub.text)
