import logging
import random
import re
import sre_constants
from common import weighted_choice, normalize, int_attribute, bool_attribute, bool_element
from errors import SamlSyntaxError, LimitError, ChanceError
from parser import Element, Restrictable
from parser.trigger.response import Response, ResponseContainer
from parser.trigger.condition import Condition


class Trigger(Element, Restrictable):
    """
    SAML Trigger object
    """
    def __init__(self, saml, element, file_path, **kwargs):
        """
        Initialize a new Trigger instance
        :param saml: The parent SAML instance
        :type  saml: Saml

        :param element: The XML Element object
        :type  element: etree._Element

        :param file_path: The absolute path to the SAML file
        :type  file_path: str

        :param kwargs: Default attributes
        """
        # Containers and default attributes
        self.priority = int_attribute(element, 'priority')
        self.normalize = bool_attribute(element, 'normalize')
        self.blocking = bool_element(element, 'blocking')

        self.pattern = kwargs['pattern'] if 'pattern' in kwargs else None
        self.groups = kwargs['groups'] if 'groups' in kwargs else None
        self.topic = kwargs['topic'] if 'topic' in kwargs else None
        self._responses = kwargs['responses'] if 'responses' in kwargs else ResponseContainer()

        # Pattern metadata
        self.pattern_is_atomic = False
        self.pattern_words = 0
        self.pattern_len = 0

        # Temporary response data
        self.stars = {
            'normalized': (),
            'case_preserved': (),
            'raw': ()
        }
        self.user = None

        # Parent __init__'s must be initialized BEFORE default attributes are assigned, but AFTER the above containers
        Restrictable.__init__(self)
        Element.__init__(self, saml, element, file_path)

        self._log = logging.getLogger('saml.parser.trigger')

    def match(self, user, message):
        """
        Returns a response message if a match is found, otherwise None
        :param user: The requesting client
        :type  user: saml.User

        :param message: The message to match
        :type  message: saml.Message

        :rtype: str or None
        """
        self._log.info('Attempting to match message against Pattern: {pattern}'
                       .format(pattern=self.pattern.pattern if hasattr(self.pattern, 'pattern') else self.pattern))
        self.user = user

        # Make sure the topic matches (if one is defined)
        if user.topic != self.topic:
            self._log.debug('User topic "{u_topic}" does not match Trigger topic "{t_topic}", skipping check'
                            .format(u_topic=user.topic, t_topic=self.topic))
            return

        # String match
        if isinstance(self.pattern, str) and str(message) == self.pattern:
            self._log.info('String Pattern matched: {match}'.format(match=self.pattern))
            return str(self._responses.random(user))

        # Regular expression match
        if hasattr(self.pattern, 'match'):
            match = self.pattern.match(str(message))
            if match:
                self._log.info('Regex pattern matched: {match}'.format(match=self.pattern.pattern))

                # Parse pattern wildcards
                self.stars['normalized'] = match.groups()
                for message_format in [message.CASE_PRESERVED, message.RAW]:
                    message.format = message_format
                    format_match = self.pattern.match(str(message))
                    if format_match:
                        self.stars[message_format] = format_match.groups()

                self._log.debug('Assigning pattern wildcards: {stars}'.format(stars=str(self.stars)))

                response = self._responses.random(user)

    # noinspection PyUnboundLocalVariable
    def _attempt_responses(self, responses, user=None):
        """
        Return a random response for this trigger
        :param user: The user to apply response reactions to
        :type  user: saml.User or None

        :param responses: A list of responses to attempt
        :type  responses: list

        :rtype: str

        :raises LimitError: All responses have an active limit enforced for the supplied user
        :raises ChanceError: All responses failed a chance test
        """
        # If we have a User, only fetch responses that are not limited
        if user:
            responses = [response for response in responses if not user.is_limited(response[0])]
        else:
            responses = self._responses

        # If all responses are limited, return now
        if not responses:
            raise LimitError

        # Fetch the response and, if a trigger chance is defined, execute it
        while True:
            response = weighted_choice(responses)
            # No chance defined
            if not response.chance:
                break

            # Chance succeeded
            if response.chance >= random.uniform(0, 100):
                self._log.info('Response had a {chance}% of being triggered and succeeded'
                               .format(chance=response.chance))
                break

            # Chance failed
            self._log.info('Response had a {chance}% of being triggered and failed, trying the next available '
                           'response'.format(chance=response.chance))
            responses = [new_response for new_response in responses if response is not new_response[0]]

            # Do we have any responses left?
            if not responses:
                self._log.info('Chance check for all Responses in this Trigger failed, giving up')
                raise ChanceError

        if user:
            response.apply_reactions(user)

        # Return the Response object
        return response

    def _add_response(self, response, weight=1):
        """
        Add a new trigger
        :param response: The Response object
        :type  response: Response or Condition

        :param weight: The weight of the response
        :type  weight: int
        """
        # If no response with this priority level has been defined yet, create a new list
        if response.priority not in self._responses:
            self._responses[response.priority] = [(response, weight)]
            return

        # Otherwise, add this trigger to an existing priority list
        self._responses[response.priority].append((response, weight))

    def _get_response(self, user=None):
        """
        Fetch a random response
        :param user: The user to apply response reactions to
        :type  user: saml.User or None

        :rtype str:

        :raises LimitError: All responses have an active limit enforced for the supplied user
        :raises ChanceError: All responses failed a chance test
        """
        end = len(self._responses) - 1

        for index, responses in enumerate([self._responses[p] for p in sorted(self._responses.keys(), reverse=True)]):
            try:
                # Evaluate any Conditions that have been set
                _responses = []
                for response in responses:
                    # If this is a standard Response, continue
                    if isinstance(response[0], Response):
                        _responses.append(response)

                    # If this is a Condition, evaluate it and append any returned results
                    if isinstance(response[0], Condition):
                        _responses.extend(response[0].evaluate(user))
                responses = _responses

                return self._attempt_responses(responses, user)
            except (LimitError, ChanceError):
                # Was this our last priority group?
                if index == end:
                    raise

                # If not, continue onto the next instead of throwing an exception
                continue

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

    @staticmethod
    def count_words(pattern):
        """
        Count the number of words in a pattern as well as the total length of those words
        :param pattern: The pattern to parse
        :type  pattern: str

        :return: The word count first, then the total length of all words
        :rtype : tuple of (int, int)
        """
        word_pattern = re.compile(r'(\b(?<![\(\)\[\]\|])\w\w*\b(?![\(\)\[\]\|]))', re.IGNORECASE)

        words = word_pattern.findall(pattern)
        word_count = len(words)
        word_len = sum(len(word) for word in words)

        return word_count, word_len

    def _parse_priority(self, element):
        """
        Parse and assign the priority for this trigger
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self._log.debug('Setting Trigger priority: {priority}'.format(priority=element.text))
        self.priority = int(element.text)

    def _parse_group(self, element):
        """
        Parse and add a group requirement for this trigger
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self._log.debug('Adding Trigger group: {group}'.format(group=element.text))
        if isinstance(self.groups, set):
            self.groups.add(element.text)
        elif self.groups is None:
            self.groups = {element.text}
        else:
            raise TypeError('Unrecognized group type, {type}: {groups}'
                            .format(type=type(self.groups), groups=str(self.groups)))

    def _parse_topic(self, element):
        """
        Parse and assign the topic for this trigger
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self._log.debug('Setting Trigger topic: {topic}'.format(topic=element.text))
        super()._parse_topic(element)

    def _parse_emotion(self, element):
        """
        Parse an emotion element
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self.emotion = normalize(element.text)

    def _parse_pattern(self, element):
        """
        Parse the trigger pattern
        :param element: The XML Element object
        :type  element: etree._Element
        """
        # If this is a raw regular expression, compile it and immediately return
        self._log.info('Parsing Trigger Pattern: ' + element.text)
        self.pattern_words, self.pattern_len = self.count_words(element.text)
        self._log.debug('Pattern contains {wc} words with a total length of {cc}'
                        .format(wc=self.pattern_words, cc=self.pattern_len))

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
            compile_as_regex = bool(match) or compile_as_regex

        # Required and optional choices
        req_choice = re.compile(r'\(([\w\s\|]+)\)')
        opt_choice = re.compile(r'\[([\w\s\|]+)\]\s?')

        if req_choice.search(self.pattern):
            def sub_required(pattern):
                patterns = pattern.group(1).split('|')
                return r'(\b{options})\b'.format(options='|'.join(patterns))

            self.pattern = req_choice.sub(sub_required, self.pattern)
            self._log.debug('Parsing Pattern required choices: ' + self.pattern)
            compile_as_regex = True

        if opt_choice.search(self.pattern):
            def sub_optional(pattern):
                patterns = pattern.group(1).split('|')
                return r'(?:\b(?:{options})\b)?\s?'.format(options='|'.join(patterns))

            self.pattern = opt_choice.sub(sub_optional, self.pattern)
            self._log.debug('Parsing Pattern optional choices: ' + self.pattern)
            compile_as_regex = True

        if compile_as_regex:
            self._log.debug('Compiling Pattern as regex')
            self.pattern = re.compile(self.pattern, re.IGNORECASE)
        else:
            self._log.debug('Pattern is atomic')
            self.pattern_is_atomic = True

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
        Parse a trigger response
        :param element: The XML Element object
        :type  element: etree._Element
        """
        # Get the responses weight
        self._log.info('Parsing new Response')
        try:
            weight = int(element.get('weight') or element.find('weight'))
            self._log.info('Setting Response weight: {weight}'.format(weight=weight))
        except TypeError:
            # Weight attribute not defined, set a default value of 1
            self._log.debug('Setting default Response weight of 1')
            weight = 1
        except ValueError:
            # A value was returned, but it wasn't an integer. This should never happen with proper schema validation.
            self._log.warn('Received non-integer value for weight attribute: {weight}'.format(element.get('weight')))
            weight = 1

        self._responses.add(Response(self, element, self.file_path, weight=weight))

    def _parse_condition(self, element):
        """
        Parse a trigger condition
        :param element: The XML Element object
        :type  element: etree._Element
        """
        self._log.info('Parsing new Condition')
        condition = Condition(self, element, self.file_path)
        for statement in condition.statements:
            for response in statement.contents:
                self._responses.add(response, condition)

    def _parse_chance(self, element):
        """
        Parse the chance of this trigger being successfully called
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

    def __str__(self):
        return self._get_response()
