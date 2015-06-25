import os
import logging
import unittest
from agentml import AgentML
from agentml.errors import VarNotDefinedError

class AgentMLTestCase(unittest.TestCase):
    """
    Base class for all AgentML test cases
    """
    def setUp(self, **kwargs):
        """
        Set up the Unit Test
        """
        self.aml = AgentML(log_level=logging.WARN)
        self.aml.load_directory(os.path.join(os.path.dirname(self.aml.script_path), 'tests', 'lang'))
        self.username = "unittest"
        self.success = 'Success!'
        self.failure = 'Failure!'

    def tearDown(self):
        pass

    def get_reply(self, message, expected, groups=None):
        """
        Test that the user's message gets the expected response
        :param message: The message to send
        :type  message: str

        :param expected: The expected response
        :type  expected: str or None

        :param groups: The trigger groups to search, defaults to only matching non-grouped triggers
        :type  groups: set or AnyGroup
        """
        reply = self.aml.get_reply(self.username, message, groups)
        self.assertEqual(reply, expected)

    def user_var(self, var, expected):
        """
        Test the value of a user variable
        :param var: The name of the variable
        :type  var: str

        :param expected: The expected value of the variable
        :type  expected: str or None
        """
        try:
            value = self.aml.get_var(var, self.username)
        except VarNotDefinedError:
            value = None

        self.assertEqual(value, expected)

    def global_var(self, var, expected):
        """
        Test the value of a global variable
        :param var: The name of the variable
        :type  var: str

        :param expected: The expected value of the variable
        :type  expected: str or None
        """
        try:
            value = self.aml.get_var(var)
        except VarNotDefinedError:
            value = None

        self.assertEqual(value, expected)

    def topic(self, expected):
        """
        Test the topic the user is currently in
        :param expected: The name of the topic
        :type  expected: str or None
        """
        user = self.aml.get_user(self.username)
        self.assertEqual(user.topic, expected)

    def chance(self, message, max_tries=250):
        """
        Test a chance statement using brute force
        :param message: The message triggering a chance statement
        :type  message: str

        :param max_tries: The maximum number of attempts to make before giving up
        :type  max_tries: int
        """
        responses = set()
        attempts = 0
        expected = {'Success!', None}

        while responses != expected:
            responses.add(self.aml.get_reply(self.username, message))
            attempts += 1

            if attempts >= max_tries:
                break

        self.assertEqual(responses, expected)
