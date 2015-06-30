from . import ConditionType

class TopicType(ConditionType):
    """
    Topic condition type
    """
    def __init__(self):
        """
        Initialize a new Topic Type instance
        """
        super().__init__('topic')

    def get(self, agentml, user=None, key=None):
        """
        Evaluate and return the current active topic
        :param user: The active user object
        :type  user: agentml.User or None

        :param agentml: The active AgentML instance
        :type  agentml: AgentML

        :param key: The user id (defaults to the current user if None)
        :type  key: str

        :return: Active topic of the user
        :rtype : str or None
        """
        user = agentml.get_user(key) if key else user
        if not user:
            return

        return user.topic
