import os
import logging
from lxml import etree
from parser import schema, attribute, int_attribute
from parser.trigger import Trigger
from parser.tags import Random, Var
from errors import SamlError, SamlSyntaxError, VarNotDefinedError, UserNotDefinedError, NoTagParserError


class Saml:
    def __init__(self):
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

        # State data
        self.topic = None
        self.mood = None

        # Define our base / system tags
        self.tags = {'random': Random, 'var': Var}

        # Containers
        self._global_vars   = {}
        # self._user_vars     = {} TBD
        self._users         = {}
        self._triggers      = {}  # TODO: Make this a list
        self._substitutions = {}

        self.load_directory(os.path.join(self.script_path, 'intelligence'))

    def load_directory(self, dir_path):
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
        :param file_path: Path to the file to load
        :type  file_path: str
        """
        self._log.info('Loading file: ' + file_path)
        saml = etree.parse(file_path)

        # Validate the file for proper SAML syntax
        valid = self._schema.validate(saml)
        if not valid:
            error = 'Invalid SAML syntax in ' + file_path
            self._log.error(error)
            raise SamlSyntaxError(error)

        # Get our root element and parse all elements inside of it
        root = etree.parse(file_path).getroot()
        for element in root:
            # Parse a standard Trigger element
            if element.tag == 'trigger':
                try:
                    self._triggers[element.find('pattern').text] = Trigger(self, element, file_path)
                except SamlError:
                    self._log.warn('Skipping pattern due to an error')

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

        for trigger in self._triggers.values():
            match = trigger.match(user, message)
            if match:
                return match

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
            if user not in self._user_vars:
                raise UserNotDefinedError

            if name not in self._user_vars[user]:
                raise VarNotDefinedError

            return self._user_vars[user][name]

        # Retrieve a global variable
        if name not in self._global_vars:
            raise VarNotDefinedError

        return self._global_vars[name]

    def set_var(self, name, value, user=None):
        """
        Set a global or user variable
        :param name: The name of the variable to set
        :type  name: str

        :param value: The variable to set
        :type  value: str

        :param user: If defining a user variable, the user identifier
        :type  user: str

        :raises UserNotDefinedError: The specified user does not exist
        """
        # Set a user variable
        if user is not None:
            if user not in self._user_vars:
                raise UserNotDefinedError

            self._user_vars[user][name] = value  # TODO
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

    def parse_tags(self, element):
        """
        Parse tags in an XML element
        :param element: The response [message] XML element
        :type  element: etree._Element

        :return: A list of strings and Tag objects in the order they are parsed
        :rtype : list of (str or parser.tags.tag,Tag)
        """
        response = []
        
        # Parse the contained tags and add their associated string objects to the response list
        for child in element:
            # Parse star tags internally
            if child.tag == 'star':
                star_index = int_attribute(child, 'index', 1)
                star_format = attribute(child, 'format', 'none')
                self._log.debug('Appending Star tag object with index {no}'.format(no=star_index))

                response.append(Star(self.trigger, star_index, star_format))
                continue

            # Make sure a parser for this tag exists
            if child.tag not in self.tags:
                self._log.warn('No parsers available for Tag "{tag}", skipping'.format(tag=child.tag))
                continue

            # Append the tag object to the response string
            tag = self.tags[child.tag]
            self._log.debug('Appending {tag} Tag object'.format(tag=child.tag.capitalize()))
            response.append(tag(self, child))

            # Append the trailing text to the response string (if there is any)
            tail = child.tail if isinstance(child.tail, str) else None
            if tail:
                self._log.debug('Appending trailing text: {text}'.format(text=tail))
                response.append(tail)

        return response

    def _parse_trigger(self, element, file_path):
        try:
            self._triggers[element.find('pattern').text] = Trigger(self, element, file_path)
        except SamlError:
            self._log.warn('Skipping pattern due to an error')


class User:
    def __init__(self, identifier):
        self.id = identifier
        self.topic = None


class Star:
    def __init__(self, trigger, index=1, star_format='none'):
        self.trigger = trigger
        self.index = index
        self.format = star_format
        self._log = logging.getLogger('saml.parser.trigger.star')

    def __str__(self):
        try:
            star = str(self.trigger.stars[self.index - 1])
        except IndexError:
            self._log.warn('No wildcard with the index {index} exists for this response'.format(index=self.index))
            return ''

        if self.format in ['title', 'upper', 'lower']:
            self._log.debug('Formatting wildcard as {format}'.format(format=self.format))
            star = getattr(star, self.format)()

        return star
