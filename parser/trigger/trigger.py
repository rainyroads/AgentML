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

        # Trigger attributes
        self.normalize = bool_attribute(element, 'normalize')
        self.substitute = bool_attribute(element, 'substitute')

        # Global / user limits
        self._global_limits = {}
        self._user_limit = {}

        # Wildcards placeholder
        self._stars = ()

        self._log = logging.getLogger('saml.trigger')
        super().__init__(saml, element, file_path)

    def match(self, user, message):
        """
        Returns a response message if a match is found, otherwise returns None
        :param user: The requesting client
        :type  user: saml.User

        :param message: The message to test
        :type  message: str

        :rtype: bool
        """
        self._log.info('Attempting to match message against Pattern: {pattern}'
                       .format(pattern=self.pattern.pattern if hasattr(self.pattern, 'pattern') else self.pattern))

        # Make sure the topic matches (if one is defined)
        if user.topic != self.topic:
            self._log.debug('User topic "{u_topic}" does not match Trigger topic "{t_topic}", skipping check'
                            .format(u_topic=user.topic, t_topic=self.topic))
            return

        if self.normalize:
            message = normalize(message)
            self._log.debug('Normalizing message: {message}'.format(message=message))

        # String match
        if isinstance(self.pattern, str) and message == self.pattern:
            self._log.info('String Pattern matched: {match}'.format(match=self.pattern))
            return self.response

        # Regular expression match
        if hasattr(self.pattern, 'match'):
            match = self.pattern.match(message)
            if match:
                self._log.info('Regex Pattern matched: {match}'.format(match=self.pattern.pattern))
                self.stars = match.groups()
                return self.response

    @property
    def response(self):
        """
        Return a random response for this trigger
        :param stars: Trigger wildcards
        :type  stars: list of str

        :rtype: str
        """
        return str(weighted_choice(self._responses))

    @property
    def stars(self):
        """
        Pulls the wildcards for this trigger event

        :rtype: tuple of str
        """
        self._log.debug('Retrieving and resetting Trigger wildcards')
        stars = self._stars
        self._stars = ()

        return stars

    @stars.setter
    def stars(self, stars):
        """
        Define the wildcards for this trigger event
        :param stars: Trigger wildcards
        :type  stars: tuple of str
        """
        self._log.debug('Setting Trigger wildcards: {wildcards}'.format(wildcards=stars))
        self._stars = stars

    @staticmethod
    def replace_wildcards(string, wildcard, regex):
        """
        Replace wildcard symbols with regular expressions
        :param wildcard:
        :type  wildcard: _sre.SRE_Pattern

        :param regex:
        :type  regex: str

        :rtype: tuple of (str, bool)
        """
        replaced = False
        match = wildcard.search(string)

        if match:
            string = wildcard.sub(regex, string)
            logging.getLogger('saml.trigger').debug('Parsing Pattern wildcards: {pattern}'.format(pattern=string))
            replaced = True

        return string, replaced

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
        self._log.info('Parsing Trigger Pattern: ' + element.text)
        regex = bool_attribute(self._element, 'regex', False)
        if regex:
            self._log.info('Attempting to compile trigger as a raw regex')
            try:
                self.pattern = re.compile(element.text)
            except sre_constants.error:
                self._log.warn('Attempted to compile an invalid regular expression in {path} ; {regex}'
                               .format(path=self.file_path, regex=element.text))
                raise SamlSyntaxError
            return

        self.pattern = normalize(element.text, True)
        self._log.debug('Normalizing pattern: ' + self.pattern)
        compile_as_regex = False

        # Wildcard patterns and replacements
        captured_wildcard = re.compile(r'(?<!\\)\(\*\)')
        wildcard = re.compile(r'(?<!\\)\*')

        capt_wild_numeric = re.compile(r'(?<!\\)\(#\)')
        wild_numeric = re.compile(r'(?<!\\)#')

        capt_wild_alpha = re.compile(r'(?<!\\)\(_\)')
        wild_alpha = re.compile(r'(?<!\\)_')

        wildcard_replacements = [
            (captured_wildcard, r'(.+)'),
            (wildcard,          r'(?:.+)'),
            (capt_wild_numeric, r'(\d+)'),
            (wild_numeric,      r'(?:\d+)'),
            (capt_wild_alpha,   r'(\w+)'),
            (wild_alpha,        r'(?:\w+)'),
        ]

        for wildcard, replacement in wildcard_replacements:
            self.pattern, match = self.replace_wildcards(self.pattern, wildcard, replacement)
            compile_as_regex = match or compile_as_regex

        # Required and optional choices
        req_choice = re.compile(r'\(([\w\|]+)\)')
        opt_choice = re.compile(r'\[([\w\s\|]+)\]\s?')

        if req_choice.search(self.pattern):
            self._log.debug('Pattern contains required choices, will be compiled as a regex')
            compile_as_regex = True

        if opt_choice.search(self.pattern):
            def sub_optional(pattern):
                patterns = pattern.group(1).split('|')
                return r'(?:{options})?\s?'.format(options='|'.join(patterns))

            self.pattern = opt_choice.sub(sub_optional, self.pattern)
            self._log.debug('Parsing Pattern optional choices: ' + self.pattern)
            compile_as_regex = True

        if compile_as_regex:
            self._log.debug('Compiling Pattern as regex')
            self.pattern = re.compile(self.pattern)
        else:
            # Replace any escaped wildcard symbols
            self._log.debug('Replacing any escaped sequences in Pattern')
            self.pattern = self.pattern.replace('\*', '*')
            self.pattern = self.pattern.replace('\#', '#')
            self.pattern = self.pattern.replace('\_', '_')

            # TODO: This needs revisiting
            self.pattern = self.pattern.replace('\(*)', '(*)')
            self.pattern = self.pattern.replace('\(#)', '(#)')
            self.pattern = self.pattern.replace('\(_)', '(_)')

    def _parse_response(self, element):
        """
        Parse a response element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        # Get the responses weight
        self._log.info('Parsing new Response')
        try:
            weight = int(element.get('weight'))
            self._log.info('Setting Response weight: {weight}'.format(weight=weight))
        except TypeError:
            # Weight attribute not defined, set a default value of 1
            self._log.debug('Setting default Response weight of 1')
            weight = 1
        except ValueError:
            # A value was returned, but it wasn't an integer. This should never happen with proper schema validation.
            self._log.warn('Received non-integer value for weight attribute: {weight}'.format(element.get('weight')))
            weight = 1

        # If the response has no tags, just store the string text
        if not len(element):
            self._responses.append((element.text, weight))
        else:
            self._responses.append((Response(self, element, self.file_path), weight))

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
