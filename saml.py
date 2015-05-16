import os
import logging
from lxml import etree
from parser import schema
from parser.trigger import Trigger
from parser.tags import Random, Var
from errors import SamlSyntaxError, VarNotDefinedError, UserNotDefinedError, NoTagParserError


class Saml:
    def __init__(self):
        # Debug logger
        self._log = logging.getLogger('saml')

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
        self._user_vars     = {}
        self._triggers      = {}
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
            # Retrieve and execute the parser method
            if element.tag == 'trigger':
                self._triggers[element.find('pattern').text] = Trigger(self, element, file_path)

    def get_reply(self, user, message):
        """
        Attempt to retrieve a reply to the provided message
        :param user: The user / client. This can be a hostmask, IP address, database ID or any other unique identifier
        :type  user: str

        :param message: The message to retrieve a reply to
        :type  message: str

        :rtype: str or None
        """
        for trigger in self._triggers.values():
            match = trigger.match(message)
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

            self._user_vars[user][name] = value
            return

        # Set a global variable
        self._global_vars[name] = value

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
