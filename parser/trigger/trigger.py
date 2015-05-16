import logging
from parser import Element, normalize
from parser.trigger.response import Response


class Trigger(Element):
    def __init__(self, saml, element, file_path, **kwargs):
        # Default attributes
        self.topic = kwargs['topic'] if 'topic' in kwargs else None
        self.emotion = kwargs['emotion'] if 'emotion' in kwargs else None

        self.pattern = kwargs['pattern'] if 'pattern' in kwargs else None
        self._responses = kwargs['responses'] if 'responses' in kwargs else []

        # Global / user limits
        self._global_limits = {}
        self._user_limit = {}

        super().__init__(saml, element, file_path)
        self._log = logging.getLogger('saml.trigger')

    def match(self, message):
        """
        Returns a response message if a match is found, otherwise returns None

        :param message: The message to test
        :type  message: str

        :rtype: bool
        """
        message = normalize(message)

        if message == self.pattern:
            return message

    def _parse_topic(self, element):
        """
        Parse a topic element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self.topic = normalize(element.text)

    def _parse_emotion(self, element):
        """
        Parse an emotion element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self.emotion = normalize(element.text)

    def _parse_pattern(self, element):
        """
        Parse a pattern element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self.pattern = normalize(element.text)

    def _parse_response(self, element):
        """
        Parse a response element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        # If the response has no tags, just store the string text
        if not len(element):
            self._responses.append(element.text)
        else:
            self._responses.append(Response(self.saml, element, self.file_path))

    def _parse_trigger(self, element):
        """
        Parse a trigger element
        :param element: The XML Element object
        :type  element: etree._Element
        """
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
                self.pattern = child.text
                continue
            # Add a response
            elif child.tag == 'response':
                # If the response has no tags, just store the string text
                if len(child) == 1:
                    self._responses.append(child.text)
                else:
                    self._responses.append(child)
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
