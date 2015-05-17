import logging
import re
import sre_constants
from parser import Element, weighted_choice, normalize, bool_attribute
from parser.trigger.response import Response
from errors import SamlSyntaxError


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

        # String match
        if isinstance(self.pattern, str) and message == self.pattern:
            return self.response

        # Regular expression match
        if hasattr(self.pattern, 'match') and self.pattern.match(message):
            return self.response

    @property
    def response(self):
        """
        Return a random response for this trigger
        :rtype: str
        """
        return str(weighted_choice(self._responses))

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
        # If this is a raw regular expression, compile it and immediately return
        regex = bool_attribute(self._element, 'regex', False)
        if regex:
            try:
                self.pattern = re.compile(element.text)
            except sre_constants.error:
                self._log.warn('Attempted to compile an invalid regular expression in {path} : {regex}'
                               .format(path=self.file_path, regex=element.text))
                raise SamlSyntaxError
            return

        self.pattern = normalize(element.text, True)

        # Wildcard patterns
        wildcard = re.compile(r'(?<!\\)\*')
        wild_numeric = re.compile(r'(?<!\\)#')
        wild_alpha = re.compile(r'(?<!\\)_')

        # General wildcards
        wildcard_match = wildcard.search(self.pattern)
        if wildcard_match:
            self.pattern = wildcard.sub(r'(.+)', self.pattern)

        # Numeric wildcards
        wild_numeric_match = wild_numeric.search(self.pattern)
        if wild_numeric_match:
            self.pattern = wild_numeric.sub(r'(\d+)', self.pattern)

        # Alpha wildcards
        wild_alpha_match = wild_alpha.search(self.pattern)
        if wild_alpha_match:
            self.pattern = wild_alpha.sub(r'(\w+)', self.pattern)

        if wildcard_match or wild_numeric_match or wild_alpha_match:
            self.pattern = re.compile(self.pattern)
        else:
            # Replace any escaped wildcard symbols
            self.pattern = self.pattern.replace('\*', '*')
            self.pattern = self.pattern.replace('\#', '#')
            self.pattern = self.pattern.replace('\_', '_')

    def _parse_response(self, element):
        """
        Parse a response element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        # Get the responses weight
        try:
            weight = int(element.get('weight'))
        except TypeError:
            # Weight attribute not defined, set a default value of 1
            weight = 1
        except ValueError:
            # A value was returned, but it wasn't an integer. This should never happen with proper schema validation.
            self._log.warn('Received non-integer value for weight attribute: ' + str(element.get('weight')))
            weight = 1

        # If the response has no tags, just store the string text
        if not len(element):
            self._responses.append((element.text, weight))
        else:
            self._responses.append((Response(self.saml, element, self.file_path), weight))

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

    def __str__(self):
        return self.response
