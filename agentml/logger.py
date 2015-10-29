import logging
from collections import deque


class InternalLogger(object):
    def __init__(self, max_entries=100):
        """
        Initialize a new base Internal Logger instance
        :param max_entries: The maximum number of log entries to retain at any given time
        :type  max_entries: int
        """
        self._max_entries = max_entries
        self._log_entries = deque(maxlen=self._max_entries)
        self._debug_log = logging.getLogger('agentml.logger')

    def add(self, *args, **kwargs):
        raise NotImplementedError('This logger class has not implemented support for adding log entries')

    @property
    def entries(self):
        """
        Return all log entries as a tuple (this is to prevent any outside manipulation of the deque instance)
        :rtype: tuple
        """
        return tuple(self._log_entries)

    def most_recent(self):
        """
        Fetch the most recent log entry
        """
        return self._log_entries[0] if len(self._log_entries) else None

    @property
    def max_entries(self):
        """
        Return the currently configured maximum number of log entries
        :rtype: int or None
        """
        return self._max_entries

    @max_entries.setter
    def max_entries(self, entries):
        """
        Chance the maximum number of retained log entries
        :param entries: The maximum number of log entries to retain at any given time
        :type  entries: int
        """
        self._debug_log.info('Changing maximum log entries from {old} to {new}'
                             .format(old=self._log_entries, new=entries))
        self._max_entries = entries

        # This is a bit awkward, but since the maxlen can't be changed after instantiation, we have to reverse the
        # deque before re-instantiating it, then reverse the new deque back in order to preserve the reverse order
        # in case any entries are truncated
        self._log_entries.reverse()
        self._log_entries = deque(self._log_entries, maxlen=self._max_entries)
        self._log_entries.reverse()

    @max_entries.deleter
    def max_entries(self):
        """
        Removes the maximum entry limit
        """
        self._debug_log.info('Removing maximum entries restriction')
        self._log_entries(deque(self._log_entries))


###############
# Requests    #
###############
class RequestLogger(InternalLogger):
    def __init__(self, max_entries=100):
        """
        Initialize a new Request Logger instance
        :param max_entries: The maximum number of log entries to retain at any given time
        :type  max_entries: int
        """
        super(RequestLogger, self).__init__(max_entries)
        self._debug_log = logging.getLogger('agentml.logger.requests')

    def add(self, user, message, groups):
        """
        Add a new log entry
        :param user: The requesting user
        :type  user: agentml.User

        :param message: The request Message instance
        :type  message: agentml.Message

        :param groups: The request groups
        :type  groups: set

        :return: The logged Request instance
        :rtype : Request
        """
        self._debug_log.debug('Logging new Request entry')
        request = Request(user, message, groups)
        self._log_entries.appendleft(request)
        return request


class Request:
    def __init__(self, user, message, groups, response=None):
        """
        Initialize a new log Request instance
        :param user: The requesting user
        :type  user: agentml.User

        :param message: The request message
        :type  message: str

        :param groups: The request groups
        :type  groups: set

        :param response: The Response associated with this Request
        :type  response: Response or None
        """
        self.user = user
        self.message = message
        self.groups = groups
        self.response = response

    def __str__(self):
        return self.message


###############
# Responses   #
###############
class ResponseLogger(InternalLogger):
    def __init__(self, max_entries=100):
        """
        Initialize a new Response Logger instance
        :param max_entries: The maximum number of log entries to retain at any given time
        :type  max_entries: int
        """
        super(ResponseLogger, self).__init__(max_entries)
        self._debug_log = logging.getLogger('agentml.logger.responses')

    def add(self, message, request):
        """
        Add a new log entry
        :param message: The request message
        :type  message: str

        :param request: The Request associated with this response
        :type  request: Request or None

        :return: The logged Response instance
        :rtype : Response
        """
        self._debug_log.debug('Logging new Response entry')
        response = Response(message, request)
        self._log_entries.appendleft(response)
        return response


class Response:
    def __init__(self, message, request=None):
        """
        Initialize a new log Request instance
        :param message: The response message
        :type  message: str

        :param request: The Request associated with this Response
        :type  request: Request or None
        """
        self.message = message
        self.request = request

    def __str__(self):
        return self.message
