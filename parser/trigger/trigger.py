import logging
from parser import Element


class Trigger(Element):
    def __init__(self, saml, element, file_path, **kwargs):
        super().__init__(saml, element, file_path)
        self._log = logging.getLogger('saml.trigger')

        # Default attributes
        self.topic = kwargs['topic'] if 'topic' in kwargs else None
        self.emotion = kwargs['emotion'] if 'emotion' in kwargs else None

        # Responses
        self._responses = kwargs['responses'] if 'responses' in kwargs else []

        # Global / user limits
        self._global_limits = {}
        self._user_limit = {}

    def _parse_topic(self, element):
        """
        Parse a topic element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self.topic = self._normalize(element.text)

    def _parse_emotion(self, element):
        """
        Parse an emotion element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self.emotion = self._normalize(element.text)

    def _parse_trigger(self, element):
        """
        Parse a trigger element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        pattern = NotImplemented
        responses = []

        for child in element:
            # Set the topic
            if child.tag == 'topic':
                self._parse_topic(child)
                continue
            # Set the emotion
            elif child.tag == 'emotion':
                self._parse_emotion(child)
                continue
            # Add a trigger
            elif child.tag == 'pattern':
                pattern = child.text
                continue
            # Add a response
            elif child.tag == 'response':
                # If the response has no tags, just store the string text
                if len(child) == 1:
                    responses.append(child.text)
                else:
                    responses.append(child)
                continue
            # Parse a reaction
            elif child.tag == 'reaction':
                self._parse_reaction(child)
                continue

    def _parse_reaction(self, element):
        """
        Parse a trigger element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        pass

    def _normalize(self, string):
        if not isinstance(string, str):
            self._log.warn('Attempted to normalize a non-string')
            return ''

        return string.strip().casefold()