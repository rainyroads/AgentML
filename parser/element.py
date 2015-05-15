from lxml import etree


class Element:
    def __init__(self, saml, element, file_path):
        """
        Base Saml Object class
        :param saml: The parent SAML instance
        :type  saml: Saml

        :param element: The XML Element object
        :type  element: etree._Element

        :param file_path: The absolute path to the SAML file
        :type  file_path: str
        """
        self.saml = saml
        self._element = element
        self.file_path = file_path

        self._parse()

    def _parse(self):
        for child in self._element:
            method_name = '_parse_' + child.tag

            if hasattr(self, method_name):
                parse = getattr(self, method_name)
                parse(child)
