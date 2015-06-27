from abc import ABCMeta, abstractmethod

class ConditionType(metaclass=ABCMeta):
    def __init__(self, name):
        """
        Initialize a new Condition Type instance
        :param name: The name of the condition type
        :type  name: str
        """
        self.name = name

    @abstractmethod
    def get(self, agentml, user=None, key=None):
        """
        Evaluate and return the current value of the condition type
        :param agentml: The active AgentML instance
        :type  agentml: AgentML

        :param user: The active user object
        :type  user: agentml.User or None

        :param key: The types key (if relevant)
        :type  key: str

        :return: Current value of the condition type
        """
        pass