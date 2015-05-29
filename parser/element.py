import logging
from lxml import etree
from parser.common import normalize, attribute


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


class TriggerResponseElement(Element):
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
        self.user_limit = None
        self.global_limit = None
        self.topic = None
        self.mood = None
        self._log = logging.getLogger('saml.parser.element')
        super().__init__(saml, element, file_path)

    def _parse_topic(self, element):
        """
        Parse a topic element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self._log.debug('Setting Response topic: {topic}'.format(topic=element.text))
        self.topic = False if element.text is None else normalize(element.text)

    def _parse_limit(self, element):
        """
        Parse a limit element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        # Is this a Global or User limit?
        limit_type = attribute(element, 'type', 'user')
        if limit_type not in ['user', 'global']:
            self._log.warn('Unrecognized limit type: {type}'.format(type=limit_type))
            return

        # If we're setting the limit using static units..
        unit_conversions = {
            'minutes': 60,
            'hours': 3600,
            'days': 86400,
            'weeks': 604800,
            'months': 2592000,
            'years': 31536000
        }
        units = attribute(element, 'units')
        if units:
            if units not in unit_conversions:
                self._log.warn('Unrecognized time unit: {unit}'.format(unit=units))
                return

            try:
                limit = float(element.text)
            except (ValueError, TypeError):
                self._log.warn('Limit must contain a valid float when using units (Invalid limit: "{limit}")'
                               .format(limit=element.text))
                return

            if limit_type == 'global':
                self.global_limit = limit * unit_conversions[units]
            elif limit_type == 'user':
                self.user_limit = limit * unit_conversions[units]

            return

        try:
            limit = float(element.text)
        except (ValueError, TypeError):
            self._log.warn('Invalid time string: {string}'.format(string=element.text))
            return

        if limit_type == 'global':
            self.global_limit = limit
        elif limit_type == 'user':
            self.user_limit = limit

    def _parse_chance(self, element):
        """
        Parse a chance element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        try:
            chance = element.text.strip('%')
            chance = float(chance)
        except (ValueError, TypeError, AttributeError):
            self._log.warn('Invalid Chance string: {chance}'.format(chance=element.text))
            return

        # Make sure the chance is a valid percentage
        if not (0 <= chance <= 100):
            self._log.warn('Chance percent must contain an integer or float between 0 and 100')
            return

        self.chance = chance