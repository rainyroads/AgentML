import os
import re
import time
import logging
from lxml import etree
from parser import schema, normalize, attribute, int_attribute
from parser.init import Init
from parser.trigger import Trigger
from parser.tags import Random, Var
from errors import SamlError, SamlSyntaxError, VarNotDefinedError, UserNotDefinedError, NoTagParserError, \
    TriggerBlockingError, LimitError


class Saml:
    def __init__(self):
        """
        Initialize a new Saml instance
        """
        # Debug logger
        self._log = logging.getLogger('saml')
        self._log.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s.%(name)s: %(message)s")
        console_logger = logging.StreamHandler()
        console_logger.setLevel(logging.DEBUG)
        console_logger.setFormatter(log_formatter)
        self._log.addHandler(console_logger)

        # Paths
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self._schema_path = os.path.join(self.script_path, 'schemas', 'saml.rng')

        # Schema validator
        with open(self._schema_path) as file:
            self._schema = schema(file.read())

        # Define our base / system tags
        self.tags = {'random': Random, 'var': Var}

        # Containers
        self._global_vars   = {}
        self._users         = {}
        self._triggers      = []
        self._substitutions = []

        # Load internal SAML files
        self.load_directory(os.path.join(self.script_path, 'intelligence'))

    def load_directory(self, dir_path):
        """
        Load all SAML files contained in a specified directory
        :param dir_path: Path to the directory
        :type  dir_path: str
        """
        self._log.info('Loading all SAML files contained in: ' + dir_path)

        # Get a list of file paths
        saml_files = []
        for root, dirs, files in os.walk(dir_path):
            saml_files += ['{root}/{file}'.format(root=root, file=file) for file in files if file.endswith('.saml')]

        # Loop through the files and load each one individually
        for file in saml_files:
            self.load_file(file)

    def load_file(self, file_path):
        """
        Load a single SAML file
        :param file_path: Path to the file
        :type  file_path: str
        """
        self._log.info('Loading file: ' + file_path)
        saml = etree.parse(file_path)

        # Validate the file for proper SAML syntax
        self._schema.assertValid(saml)

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
                    defaults['group'] = child.get('name')
                    parse_element(child)
                    continue

                # Set the topic
                if child.tag == 'topic':
                    self._log.info('Setting Trigger topic: {topic}'.format(topic=child.get('name')))
                    defaults['topic'] = child.get('name')
                    parse_element(child)
                    continue

                # Set the emotion
                if child.tag == 'emotion':
                    self._log.info('Setting Trigger emotion: {emotion}'.format(emotion=child.get('name')))
                    defaults['emotion'] = child.get('name')
                    parse_element(child)
                    continue

                # Parse a standard Trigger element
                if child.tag == 'trigger':
                    try:
                        self._triggers.append(Trigger(self, child, file_path, **defaults))
                    except SamlError:
                        self._log.warn('Skipping Trigger due to an error', exc_info=True)
                    finally:
                        # Reset the dictionary of default attributes for the next trigger iteration
                        self._log.debug('Resetting default Trigger attributes')
                        defaults.clear()

        # Begin element iteration by parsing the root element
        parse_element(root)

    def get_reply(self, user, message):
        """
        Attempt to retrieve a reply to the provided message
        :param user: The user / client. This can be a hostmask, IP address, database ID or any other unique identifier
        :type  user: str

        :param message: The message to retrieve a reply to
        :type  message: str

        :rtype: str or None
        """
        user = self.get_user(user)

        # Fetch triggers in our topic, and make sure we're not in an empty topic
        triggers = [trigger for trigger in self._triggers if user.topic == trigger.topic]
        if not triggers and user.topic is not None:
            self._log.warn('User "{user}" was in an empty topic: {topic}'.format(user=user.id, topic=user.topic))
            user.topic = None
            triggers = [trigger for trigger in self._triggers if user.topic == trigger.topic]

        # It's impossible to get anywhere if there are no empty topic triggers available to guide us
        if not triggers:
            raise SamlError('There are no empty topic triggers defined, unable to continue')

        for trigger in triggers:
            try:
                match = trigger.match(user, Message(message))
            except TriggerBlockingError:
                return

            if match:
                return match

    def set_substitution(self, word, substitution):
        """
        Add a word substitution
        :param word: The word to replace
        :type  word: str

        :param substitution: The word's substitution
        :type  substitution: str
        """
        word = re.escape(normalize(word))
        substitution = normalize(substitution)

        sub = (re.compile(r'\b{word}\b'.format(word=word)), substitution)

        if sub not in self._substitutions:
            self._log.info('Appending new word substitution: "{word}" => "{sub}"'.format(word=word, sub=substitution))
            self._substitutions.append(sub)

    def parse_substitutions(self, message):
        """
        Parse substitutions in a supplied message
        :param message: The message to parse
        :type  message: str

        :return: Substituted message
        :rtype : str
        """
        for word, substitution in self._substitutions:
            message = word.sub(substitution, message)

        self._log.info('Message substitutions processed: {message}'.format(message=message))
        return message

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

    def get_user(self, identifier):
        # Does this user already exist?
        if identifier in self._users:
            return self._users[identifier]

        # User does not exist, so let's create a new one
        self._users[identifier] = User(identifier)
        return self._users[identifier]

    def get_tag(self, element):
        """
        Retrieve an instantiated Tag object
        :param element: The tag XML element
        :type  element: etree._Element

        :rtype: parser.tags.Tag

        :raise NoTagParserError: No parser for this tag has been defined
        """
        if element.tag not in self.tags:
            raise NoTagParserError

    def set_tag(self):
        pass  # TODO

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
        head = element.text if isinstance(element.text, str) else None
        if head:
            if head.strip():
                self._log.debug('Appending heading text: {text}'.format(text=head))
            response.append(head)

        # Internal method for appending an elements tail to the response list
        def append_tail(e):
            tail = e.tail if isinstance(e.tail, str) else None
            if tail:
                if tail.strip():
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
            if child.tag not in self.tags:
                self._log.warn('No parsers available for Tag "{tag}", skipping'.format(tag=child.tag))
                continue

            # Append the tag object to the response string
            tag = self.tags[child.tag]
            self._log.debug('Appending {tag} Tag object'.format(tag=child.tag.capitalize()))
            response.append(tag(trigger, child))

            # Append the trailing text to the response string (if there is any)
            append_tail(child)

        return response

    def _parse_trigger(self, element, file_path):
        try:
            self._triggers[element.find('pattern').text] = Trigger(self, element, file_path)
        except SamlError:
            self._log.warn('Skipping pattern due to an error')


class Message:
    """
    Message container object
    """
    NORMALIZED = 'normalized'
    PRESERVE_CASE = 'preserve_case'
    RAW = 'raw'

    formats = [NORMALIZED, PRESERVE_CASE, RAW]

    def __init__(self, message, message_format=NORMALIZED):
        """
        Initialize a new Message instance
        :param message: The message being parsed
        :type  message: str

        :param message_format: The message format to return when the object is interpreted as a string
        :type  message_format: str
        """
        self._log = logging.getLogger('saml.message')
        self._format = message_format

        # Parsed (and un-parsed) message containers
        self._log.debug('Parsing raw message: {message}'.format(message=message))
        self._messages = {
            'normalized_message': normalize(message),
            'preserve_case_message': normalize(message, preserve_case=True),
            'raw_message': message
        }

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
        self._log = logging.getLogger('saml.user')
        self._log.info('Creating new user: {id}'.format(id=identifier))

        # User attributes
        self.id = identifier
        self.topic = None
        self._vars = {}
        self._limits = {}  # Dictionary of trigger id()'s as keys, tuple of limit expiration's and blocking as values

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
        :param identifier: The id() of the Trigger or Response object
        :type  identifier: int

        :param expires_at: The limit expiration as a Unix timestamp
        :type  expires_at: float

        :param blocking: When True and a limit is triggered, no other Triggers will be attempted
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

    def is_limited(self, trigger):
        """
        Test whether or not there is an active User limit for the specified Trigger instance
        :param trigger: The Trigger to test for a limit
        :type  trigger: parser.trigger.trigger.Trigger

        :return: True if there is a limit enforced, otherwise False
        :rtype : bool
        """
        # Get the object ID of the Trigger instance
        trigger_id = id(trigger)

        # If there is a limit for this Trigger assigned, make sure it hasn't expired
        if trigger_id in self._limits:
            limit, blocking = self._limits[trigger_id]
            if time.time() < limit:
                # Limit exists and is active, return True
                self._log.debug('User "{uid}" has a limit enforced for Object {oid}'
                                .format(uid=self.id, oid=trigger_id))
                if blocking:
                    raise LimitError
                return True
            else:
                # Limit has expired, remove it
                del self._limits[trigger_id]

        # We're still here, so there are no active limits. Return False
        self._log.debug('User "{uid}" has no limit enforced for Object {oid}'.format(uid=self.id, oid=trigger_id))
        return False


class Star:
    """
    Wildcard object
    """
    def __init__(self, trigger, index=1, star_format='normalized'):
        """
        Initialize a new Star wildcard tag object
        :param trigger: SAML Trigger instance
        :type  trigger: parser.trigger.trigger.Trigger

        :param index: The wildcard index to retrieve (Indexes start at 1, not 0)
        :type  index: int

        :param star_format: The formatting to apply to the text value. Can be any valid Python string method
        :type  star_format: str
        """
        self.trigger = trigger
        self.index = index
        self.format = star_format
        self._log = logging.getLogger('saml.star')

    def __str__(self):
        try:
            if self.format in ['preserve_case', 'raw']:
                self._log.debug('Formatting wildcard as {format}'.format(format=self.format))
                star = str(self.trigger.stars[self.format][self.index - 1])
            else:
                star = str(self.trigger.stars['normalized'][self.index - 1])
        except IndexError:
            self._log.warn('No wildcard with the index {index} exists for this response'.format(index=self.index))
            return ''

        if self.format in ['title', 'upper', 'lower']:
            self._log.debug('Formatting wildcard as {format}'.format(format=self.format))
            star = getattr(star, self.format)()

        return star
