from __future__ import print_function, unicode_literals
from six import string_types
import os
import re
import logging
from time import time
from lxml import etree
# from typewriter import typewrite
from agentml.common import schema, normalize, attribute, int_attribute, newlines_to_spaces
from agentml.parser.init import Init
from agentml.parser.trigger import Trigger
from agentml.parser.tags import Condition, Redirect, Random, Var, Tag
from agentml.parser.trigger.condition.types import UserVarType, GlobalVarType, TopicType, UserType, ConditionType
from agentml.logger import RequestLogger, ResponseLogger
from agentml.constants import AnyGroup
from agentml.errors import AgentMLError, VarNotDefinedError, UserNotDefinedError, ParserBlockingError, LimitError

__author__     = "Makoto Fujimoto"
__copyright__  = 'Copyright 2015, Makoto Fujimoto'
__license__    = "MIT"
__version__    = "0.3"
__maintainer__ = "Makoto Fujimoto"


class AgentML:
    def __init__(self, log_level=logging.WARN):
        """
        Initialize a new AgentML instance

        :param log_level: The debug logging level, defaults to logging.WARN
        :type  log_level: int
        """
        # Debug logger
        self._log = logging.getLogger('agentml')
        self._log.setLevel(log_level)
        log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s.%(name)s: %(message)s")
        console_logger = logging.StreamHandler()
        console_logger.setLevel(log_level)
        console_logger.setFormatter(log_formatter)
        self._log.addHandler(console_logger)

        # Paths
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self._schema_path = os.path.join(self.script_path, 'schemas', 'agentml.rng')

        # Schema validator
        with open(self._schema_path) as file:
            self._schema = schema(file.read())

        # Define our base / system tags
        self._tags = {'condition': Condition, 'redirect': Redirect, 'random': Random, 'var': Var}
        self.conditions = {'user_var': UserVarType(), 'global_var': GlobalVarType(), 'topic': TopicType(),
                           'user': UserType()}

        # Containers
        self._global_vars   = {}
        self._limits        = {}
        self._users         = {}
        self._triggers      = {}
        self._substitutions = []

        # Loggers
        self.request_log = RequestLogger()
        self.response_log = ResponseLogger()

        # Triggers must be sorted before replies are retrieved
        self.sorted = False
        self._sorted_triggers = []

        # Load internal AgentML files
        self.load_directory(os.path.join(self.script_path, 'intelligence'))

    def load_directory(self, dir_path):
        """
        Load all AgentML files contained in a specified directory
        :param dir_path: Path to the directory
        :type  dir_path: str
        """
        self._log.info('Loading all AgentML files contained in: ' + dir_path)

        # Get a list of file paths
        aml_files = []
        for root, dirs, files in os.walk(dir_path):
            aml_files += ['{root}/{file}'.format(root=root, file=file)
                          for file in sorted(files) if file.endswith('.aml')]

        # Loop through the files and load each one individually
        for file in aml_files:
            self.load_file(file)

    def load_file(self, file_path):
        """
        Load a single AgentML file
        :param file_path: Path to the file
        :type  file_path: str
        """
        self._log.info('Loading file: ' + file_path)
        agentml = etree.parse(file_path)

        # Validate the file for proper AgentML syntax
        self._schema.assertValid(agentml)

        # Get our root element and parse all elements inside of it
        root = etree.parse(file_path).getroot()
        defaults = {}

        def parse_element(element):
            for child in element:
                # Initialization
                if child.tag == 'init':
                    Init(self, child, file_path)

                # Set the group
                if child.tag == 'group':
                    self._log.info('Setting Trigger group: {group}'.format(group=child.get('name')))
                    defaults['groups'] = {child.get('name')}  # TODO
                    parse_element(child)
                    del defaults['groups']
                    continue

                # Set the topic
                if child.tag == 'topic':
                    self._log.info('Setting Trigger topic: {topic}'.format(topic=child.get('name')))
                    defaults['topic'] = child.get('name')
                    parse_element(child)
                    del defaults['topic']
                    continue

                # Set the emotion
                if child.tag == 'emotion':
                    self._log.info('Setting Trigger emotion: {emotion}'.format(emotion=child.get('name')))
                    defaults['emotion'] = child.get('name')
                    parse_element(child)
                    del defaults['emotion']
                    continue

                # Parse a standard Trigger element
                if child.tag == 'trigger':
                    try:
                        self.add_trigger(Trigger(self, child, file_path, **defaults))
                    except AgentMLError:
                        self._log.warn('Skipping Trigger due to an error', exc_info=True)

        # Begin element iteration by parsing the root element
        parse_element(root)

    def sort(self):
        """
        Sort triggers and their associated responses
        """
        # Sort triggers by word and character length first
        for priority, triggers in self._triggers.items():
            self._log.debug('Sorting priority {priority} triggers'.format(priority=priority))

            # Get and sort our atomic and wildcard patterns
            atomics = [trigger for trigger in triggers if trigger.pattern_is_atomic]
            wildcards = [trigger for trigger in triggers if not trigger.pattern_is_atomic]

            atomics = sorted(atomics, key=lambda trigger: (trigger.pattern_words, trigger.pattern_len), reverse=True)
            wildcards = sorted(wildcards, key=lambda trigger: (trigger.pattern_words, trigger.pattern_len),
                               reverse=True)

            # Replace our sorted triggers
            self._triggers[priority] = atomics + wildcards

        # Finally, sort triggers by priority
        self._sorted_triggers = []

        for triggers in [self._triggers[priority] for priority in sorted(self._triggers.keys(), reverse=True)]:
            for trigger in triggers:
                self._sorted_triggers.append(trigger)

        self.sorted = True

    def get_reply(self, user, message, groups=None):
        """
        Attempt to retrieve a reply to the provided message
        :param user: The user / client. This can be a hostmask, IP address, database ID or any other unique identifier
        :type  user: str

        :param message: The message to retrieve a reply to
        :type  message: string_types

        :param groups: The trigger groups to search, defaults to only matching non-grouped triggers
        :type  groups: set or AnyGroup

        :rtype: str or None
        """
        # Make sure triggers have been sorted since the most recent trigger was added
        if not self.sorted:
            self.sort()

        user = self.get_user(user)
        groups = groups or {None}

        # Log this request
        message = Message(self, message)
        request_log_entry = self.request_log.add(user, message, groups)

        # Fetch triggers in our topic and make sure we're not in an empty topic
        triggers = [trigger for trigger in self._sorted_triggers if user.topic == trigger.topic]

        if not triggers and user.topic is not None:
            self._log.warn('User "{user}" was in an empty topic: {topic}'.format(user=user.id, topic=user.topic))
            user.topic = None
            triggers = [trigger for trigger in self._sorted_triggers if user.topic == trigger.topic]

        # It's impossible to get anywhere if there are no empty topic triggers available to guide us
        if not triggers:
            raise AgentMLError('There are no empty topic triggers defined, unable to continue')

        # Fetch triggers in our group and make sure we're not in an empty topic
        if groups is not AnyGroup:
            triggers = [trigger for trigger in triggers if groups.issuperset(trigger.groups or {None})]

        if not triggers:
            if not user.topic:
                self._log.info('There are no topicless triggers matching the specific groups available, giving up')
                return

            self._log.info('The topic "{topic}" has triggers, but we are not in the required groups to match them. '
                           'Resetting topic to None and retrying'.format(topic=user.topic, groups=str(groups)))
            user.topic = None
            triggers = [trigger for trigger in self._sorted_triggers if user.topic == trigger.topic]

        for trigger in triggers:
            try:
                match = trigger.match(user, message)
            except ParserBlockingError:
                return

            if match:
                message = str(match)
                request_log_entry.response = self.response_log.add(message, request_log_entry)
                return message

        # If we're still here, no reply was matched. If we're in a topic, exit and retry
        if user.topic:
            self._log.info('No reply matched in the topic "{topic}", resetting topic to None and retrying'
                           .format(topic=user.topic))
            user.topic = None

            # noinspection PyTypeChecker
            return self.get_reply(user.id, message.raw)

    def add_trigger(self, trigger):
        """
        Add a new trigger
        :param trigger: The Trigger object
        :type  trigger: Trigger
        """
        # Make sure triggers are re-sorted before a new reply can be requested
        self.sorted = False

        # If no trigger with this priority level has been defined yet, create a new list
        if trigger.priority not in self._triggers:
            self._triggers[trigger.priority] = [trigger]
            return

        # Otherwise, add this trigger to an existing priority list
        self._triggers[trigger.priority].append(trigger)

    def set_substitution(self, word, substitution):
        """
        Add a word substitution
        :param word: The word to replace
        :type  word: str

        :param substitution: The word's substitution
        :type  substitution: str
        """
        # Parse the word and its substitution
        raw_word = re.escape(word)
        raw_substitution = substitution

        case_word = re.escape(normalize(word, preserve_case=True))
        case_substitution = normalize(substitution, preserve_case=True)

        word = re.escape(normalize(word))
        substitution = normalize(substitution)

        # Compile and group the regular expressions
        raw_sub = (re.compile(r'\b{word}\b'.format(word=raw_word), re.IGNORECASE), raw_substitution)
        case_sub = (re.compile(r'\b{word}\b'.format(word=case_word), re.IGNORECASE), case_substitution)
        sub = (re.compile(r'\b{word}\b'.format(word=word), re.IGNORECASE), substitution)

        sub_group = (sub, case_sub, raw_sub)

        # Make sure this substitution hasn't already been processed and add it to the substitutions list
        if sub_group not in self._substitutions:
            self._log.info('Appending new word substitution: "{word}" => "{sub}"'.format(word=word, sub=substitution))
            self._substitutions.append(sub_group)

    # noinspection PyUnboundLocalVariable
    def parse_substitutions(self, messages):
        """
        Parse substitutions in a supplied message
        :param messages: A tuple messages being parsed (normalized, case preserved, raw)
        :type  messages: tuple of (str, str, str)

        :return: Substituted messages (normalized, case preserved, raw)
        :rtype : tuple of (str, str, str)
        """
        # If no substitutions have been defined, just normalize the message
        if not self._substitutions:
            self._log.info('No substitutions to process')
            return messages

        self._log.info('Processing message substitutions')

        def substitute(sub_group, sub_message):
            word, substitution = sub_group
            return word.sub(substitution, sub_message)

        normalized, preserve_case, raw = messages
        for sub_normalized, sub_preserve_case, sub_raw in self._substitutions:
            normalized = substitute(sub_normalized, normalized)
            preserve_case = substitute(sub_preserve_case, preserve_case)
            raw = substitute(sub_raw, raw)

        return normalized, preserve_case, raw

    def get_var(self, name, user=None):
        """
        Retrieve a global or user variable
        :param name: The name of the variable to retrieve
        :type  name: str

        :param user: If retrieving a user variable, the user identifier
        :type  user: str or None

        :rtype: str

        :raises UserNotDefinedError: The specified user does not exist
        :raises VarNotDefinedError: The requested variable has not been defined
        """
        # Retrieve a user variable
        if user is not None:
            if user not in self._users:
                raise UserNotDefinedError

            return self._users[user].get_var(name)

        # Retrieve a global variable
        if name not in self._global_vars:
            raise VarNotDefinedError

        return self._global_vars[name]

    def set_var(self, name, value, user=None):
        """
        Set a global or user variable
        :param name: The name of the variable to set
        :type  name: str

        :param value: The value of the variable to set
        :type  value: str

        :param user: If defining a user variable, the user identifier
        :type  user: str

        :raises UserNotDefinedError: The specified user does not exist
        """
        # Set a user variable
        if user is not None:
            if user not in self._users:
                raise UserNotDefinedError

            self._users[user].set_var(name, value)
            return

        # Set a global variable
        self._global_vars[name] = value

    def set_limit(self, identifier, expires_at, blocking=False):
        """
        Set a new global trigger or response limit
        :param identifier: The Trigger or Response object
        :type  identifier: parser.trigger.Trigger or parser.trigger.response.Response

        :param expires_at: The limit expiration as a Unix timestamp
        :type  expires_at: float

        :param blocking: When True and a limit is triggered, no other Trigger or Response's will be attempted
        :type  blocking: bool
        """
        self._limits[identifier] = (expires_at, blocking)

    def clear_limit(self, identifier=None):
        """
        Remove a single limit or all defined limits
        :param identifier: The identifier to clear limits for, or if no identifier is supplied, clears ALL limits
        :type  identifier: int

        :return: True if a limit was successfully found and removed, False if no limit could be matched for removal
        :rtype : bool
        """
        # Remove a single limit
        if identifier:
            if identifier in self._limits:
                del self._limits[identifier]
                return True
            else:
                return False

        # Remove all limits
        if self._limits:
            self._limits.clear()
            return True
        else:
            return False

    def is_limited(self, identifier):
        """
        Test whether or not there is an active global limit for the specified Trigger or Response instance
        :param identifier: The Trigger or Response object
        :type  identifier: parser.trigger.Trigger or parser.trigger.response.Response

        :return: True if there is a limit enforced, otherwise False
        :rtype : bool
        """
        # If there is a limit for this Trigger assigned, make sure it hasn't expired
        if identifier in self._limits:
            limit, blocking = self._limits[identifier]
            if time() < limit:
                # Limit exists and is active, return True
                self._log.debug('Global limit enforced for Object {oid}'
                                .format(oid=id(identifier)))
                if blocking:
                    raise LimitError
                return True
            else:
                # Limit has expired, remove it
                del self._limits[identifier]

        # We're still here, so there are no active limits. Return False
        self._log.debug('No global limit enforced for Object {oid}'.format(oid=id(identifier)))
        return False

    def get_user(self, identifier):
        # Does this user already exist?
        if identifier in self._users:
            return self._users[identifier]

        # User does not exist, so let's create a new one
        self._users[identifier] = User(identifier)
        return self._users[identifier]

    def add_condition(self, name, cond_class):
        """
        Add a new custom condition type parser
        :param name: The name of the condition type
        :type  name: str

        :param cond_class: The Class
        :return:
        """
        # Has this condition type already been defined?
        if name in self.conditions:
            self._log.warn('Overwriting an existing Condition Type class: {type}'.format(type=name))

        if not issubclass(cond_class, ConditionType):
            self._log.error('Condition Type class must implement the base ConditionType interface, please review the '
                            'documentation on defining custom condition types. (Refusing to set the condition type '
                            '"{type}")'.format(type=name))
            return

        self.conditions[name] = cond_class(name)

    def set_tag(self, name, tag_class):
        """
        Define a new tag parser method
        :param name: The name of the tag
        :type  name: str

        :param tag_class: The Tag class, this must be a subclass of base parser.tags.Tag
        :type  tag_class: Tag
        """
        # Has this tag already been defined?
        if name in self._tags:
            self._log.warn('Overwriting an existing Tag class: {tag}'.format(tag=name))

        # Make sure the tag class adhered to the base Tag interface
        if not issubclass(tag_class, Tag):
            self._log.error('Tag class must implement the base Tag interface, please review the documentation on '
                            'defining custom tags. (Refusing to set the tag "{tag}")'.format(tag=name))
            return

        self._tags[name] = tag_class

    def parse_tags(self, element, trigger):
        """
        Parse tags in an XML element
        :param element: The response [message] XML element
        :type  element: etree._Element

        :return: A list of strings and Tag objects in the order they are parsed
        :rtype : list of (str or parser.tags.tag,Tag)
        """
        response = []

        # Add the starting text to the response list
        head = element.text if isinstance(element.text, string_types) else None
        if head:
            if head.strip():
                head = newlines_to_spaces(head)
                self._log.debug('Appending heading text: {text}'.format(text=head))
            response.append(head)

        # Internal method for appending an elements tail to the response list
        def append_tail(e):
            tail = e.tail if isinstance(e.tail, string_types) else None
            if tail:
                if tail.strip():
                    tail = newlines_to_spaces(tail)
                    self._log.debug('Appending trailing text: {text}'.format(text=tail))
                response.append(tail)

        # Parse the contained tags and add their associated string objects to the response list
        for child in element:
            # Parse star tags internally
            if child.tag == 'star':
                star_index = int_attribute(child, 'index', 1)
                star_format = attribute(child, 'format', 'none')
                self._log.debug('Appending Star tag object with index {no}'.format(no=star_index))

                response.append(Star(trigger, star_index, star_format))
                append_tail(child)
                continue

            # Make sure a parser for this tag exists
            if child.tag not in self._tags:
                self._log.warn('No parsers available for Tag "{tag}", skipping'.format(tag=child.tag))
                continue

            # Append the tag object to the response string
            tag = self._tags[child.tag]
            self._log.debug('Appending {tag} Tag object'.format(tag=child.tag.capitalize()))
            response.append(tag(trigger, child))

            # Append the trailing text to the response string (if there is any)
            append_tail(child)

        return response

    def interpreter(self):
        """
        Launch an AML interpreter session for testing
        """
        while True:
            message = input('[#] ')
            if message.lower().strip() == 'exit':
                break

            reply = self.get_reply('#interpreter#', message)
            if not reply:
                print('No reply received.', end='\n\n')
                continue

            # typewrite(reply, end='\n\n') TODO
            print(reply, end='\n\n')


class Message(object):
    """
    Message container object
    """
    NORMALIZED = 'normalized'
    CASE_PRESERVED = 'case_preserved'
    RAW = 'raw'

    formats = [NORMALIZED, CASE_PRESERVED, RAW]

    def __init__(self, aml, message, message_format=NORMALIZED):
        """
        Initialize a new Message instance
        :param aml: The parent AgentML instance
        :type  aml: AgentML

        :param message: The message being parsed
        :type  message: str

        :param message_format: The message format to return when the object is interpreted as a string
        :type  message_format: str
        """
        self._log = logging.getLogger('agentml.message')
        self._format = message_format
        self.aml = aml

        # Parsed (and un-parsed) message containers
        self._log.debug('Parsing raw message: {message}'.format(message=message))
        messages = self.aml.parse_substitutions((normalize(message), normalize(message, preserve_case=True), message))
        self._messages = {
            'normalized_message': messages[0],
            'case_preserved_message': messages[1],
            'raw_message': messages[2]
        }
        self._log.debug('Normalized message processed: {msg}'.format(msg=self._messages['normalized_message']))
        self._log.debug('Case preserved message processed: {msg}'.format(msg=self._messages['case_preserved_message']))
        self._log.debug('Raw message processed: {msg}'.format(msg=self._messages['raw_message']))

    @property
    def format(self):
        """
        Return the currently set message format
        """
        return self._format

    @format.setter
    def format(self, message_format):
        """
        Set the message format
        :param message_format: The format to set
        :type  message_format: str
        """
        if message_format not in self.formats:
            self._log.error('Invalid Message format specified: {format}'.format(format=message_format))
            return

        self._log.debug('Setting message format to {format}'.format(format=message_format))
        self._format = message_format

    @property
    def normalized(self):
        """
        Return the normalized message
        """
        return self._messages['normalized_message']

    @property
    def case_preserved(self):
        """
        Return the case preserved normalized message
        """
        return self._messages['case_preserved_message']

    @property
    def raw(self):
        """
        Return the raw message
        """
        return self._messages['raw_message']

    def __str__(self):
        return self._messages['{format}_message'.format(format=self._format)]


class User:
    """
    User session object
    """
    def __init__(self, identifier):
        """
        Initialize a new User instance
        :param identifier: The unique identifier for the User. Examples include IRC hostmasks, IP addresses, and DB ID's
        :type  identifier: str
        """
        self._log = logging.getLogger('agentml.user')
        self._log.info('Creating new user: {id}'.format(id=identifier))

        # User attributes
        self.id = identifier
        self.topic = None
        self._vars = {}
        self._limits = {}  # Dictionary of objects as keys, tuple of limit expiration's and blocking as values

    def get_var(self, name):
        """
        Retrieve a variable assigned to this user
        :param name: The name of the variable to retrieve
        :type  name: str

        :rtype: str

        :raises VarNotDefinedError: The requested variable has not been defined
        """
        if name not in self._vars:
            raise VarNotDefinedError

        return self._vars[name]

    def set_var(self, name, value):
        """
        Set a variable for this user
        :param name: The name of the variable to set
        :type  name: str

        :param value: The value of the variable to set
        :type  value: str
        """
        self._vars[name] = value

    def set_limit(self, identifier, expires_at, blocking=False):
        """
        Set a new trigger or response limit
        :param identifier: The Trigger or Response object
        :type  identifier: parser.trigger.Trigger or parser.trigger.response.Response

        :param expires_at: The limit expiration as a Unix timestamp
        :type  expires_at: float

        :param blocking: When True and a limit is triggered, no other Trigger or Response's will be attempted
        :type  blocking: bool
        """
        self._limits[identifier] = (expires_at, blocking)

    def clear_limit(self, identifier=None):
        """
        Remove a single limit or all defined limits
        :param identifier: The identifier to clear limits for, or if no identifier is supplied, clears ALL limits
        :type  identifier: int

        :return: True if a limit was successfully found and removed, False if no limit could be matched for removal
        :rtype : bool
        """
        # Remove a single limit
        if identifier:
            if identifier in self._limits:
                del self._limits[identifier]
                return True
            else:
                return False

        # Remove all limits
        if self._limits:
            self._limits.clear()
            return True
        else:
            return False

    def is_limited(self, identifier):
        """
        Test whether or not there is an active User limit for the specified Trigger or Response instance
        :param identifier: The Trigger or Response object
        :type  identifier: parser.trigger.Trigger or parser.trigger.response.Response

        :return: True if there is a limit enforced, otherwise False
        :rtype : bool
        """
        # If there is a limit for this Trigger assigned, make sure it hasn't expired
        if identifier in self._limits:
            limit, blocking = self._limits[identifier]
            if time() < limit:
                # Limit exists and is active, return True
                self._log.debug('User "{uid}" has a limit enforced for Object {oid}'
                                .format(uid=self.id, oid=id(identifier)))
                if blocking:
                    raise LimitError
                return True
            else:
                # Limit has expired, remove it
                del self._limits[identifier]

        # We're still here, so there are no active limits. Return False
        self._log.debug('User "{uid}" has no limit enforced for Object {oid}'.format(uid=self.id, oid=id(identifier)))
        return False


class Star:
    """
    Wildcard object
    """
    def __init__(self, trigger, index=1, star_format='normalized'):
        """
        Initialize a new Star wildcard tag object
        :param trigger: AgentML Trigger instance
        :type  trigger: parser.trigger.trigger.Trigger

        :param index: The wildcard index to retrieve (Indexes start at 1, not 0)
        :type  index: int

        :param star_format: The formatting to apply to the text value. Can be any valid Python string method
        :type  star_format: str
        """
        self.trigger = trigger
        self.index = index
        self.format = star_format
        self._log = logging.getLogger('agentml.star')

    def __str__(self):
        try:
            if self.format in ['case_preserved', 'raw']:
                self._log.debug('Formatting wildcard as {format}'.format(format=self.format))
                star = str(self.trigger.stars[self.format][self.index - 1])
            else:
                star = str(self.trigger.stars['normalized'][self.index - 1])
        except IndexError:
            self._log.warn('No wildcard with the index {index} exists for this response'.format(index=self.index))
            return ''

        if self.format in ['title', 'capitalize', 'upper', 'lower']:
            self._log.debug('Formatting wildcard as {format}'.format(format=self.format))
            star = getattr(star, self.format)()

        return star
