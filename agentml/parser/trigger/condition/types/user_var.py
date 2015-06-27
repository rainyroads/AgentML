from . import ConditionType
from agentml.errors import VarNotDefinedError

class UserVarType(ConditionType):
    """
    User Variable condition type
    """
    def __init__(self):
        """
        Initialize a new User Var Type instance
        """
        super().__init__('user_var')

    def get(self, agentml, user=None, key=None):
        """
        Evaluate and return the current value of a user variable
        :param user: The active user object
        :type  user: agentml.User or None

        :param agentml: The active AgentML instance
        :type  agentml: AgentML

        :param key: The variables key
        :type  key: str

        :return: Current value of the user variable (or None if the variable has not been set)
        :rtype : str or None
        """
        if not user or not key:
            return

        try:
            return user.get_var(key)
        except VarNotDefinedError:
            return
