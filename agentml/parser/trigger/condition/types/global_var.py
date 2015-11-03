from . import ConditionType
from agentml.errors import VarNotDefinedError


class GlobalVarType(ConditionType):
    """
    Global Variable condition type
    """
    def __init__(self):
        """
        Initialize a new Global Var Type instance
        """
        super(GlobalVarType, self).__init__('global_var')

    def get(self, agentml, user=None, key=None):
        """
        Evaluate and return the current value of a global variable
        :param user: The active user object
        :type  user: agentml.User or None

        :param agentml: The active AgentML instance
        :type  agentml: AgentML

        :param key: The variables key
        :type  key: str

        :return: Current value of the global variable (or None if the variable has not been set)
        :rtype : str or None
        """
        if not key:
            return

        try:
            return agentml.get_var(key)
        except VarNotDefinedError:
            return
