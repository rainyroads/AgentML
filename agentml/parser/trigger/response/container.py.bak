import logging
import random
from collections import OrderedDict
from agentml.common import weighted_choice
from agentml.errors import LimitError, ChanceError


class ResponseContainer(object):
    """
    Container for Response objects
    """
    def __init__(self):
        """
        Initialize a new Response Container
        """
        # Responses are contained in an ordered dictionary, with the keys being the priority level
        self._responses = OrderedDict()
        self._conditionals = {}  # keys contain response id()'s, values contain Condition objects
        self.sorted = False  # Priority levels need to be sorted after parsing before they can be iterated
        self._log = logging.getLogger('agentml.parser.trigger.response.container')

    def _sort(self):
        """
        Sort the response dictionaries priority levels for ordered iteration
        """
        self._log.debug('Sorting responses by priority')
        self._responses = OrderedDict(sorted(list(self._responses.items()), reverse=True))
        self.sorted = True

    def add(self, response, condition=None):
        """
        Add a new Response object
        :param response: The Response object
        :type  response: parser.trigger.response.Response

        :param condition: An optional Conditional statement for the Response
        :type  condition: parser.condition.Condition or None
        """
        self._log.info('Adding a new response with the priority level {priority}'.format(priority=response.priority))
        # If this is the first time we are seeing this priority level, ready a new response list
        if response.priority not in self._responses:
            self.sorted = False  # Only reset sorted flag on a new priority definition for efficiency
            self._responses[response.priority] = []

        # If this response requires a condition be met, assign it to the Response object directly
        if condition:
            self._log.debug('Response has a condition defined')
            self._conditionals[response] = condition

        self._responses[response.priority].append(response)

    def random(self, user=None):
        """
        Retrieve a random Response
        :param user: The user to test for active limitations and to apply response actions on
        :type  user: agentml.User or None

        :return: A randomly selected Response object
        :rtype : parser.trigger.response.Response
        """
        if not self.sorted:
            self._sort()

        self._log.info('Attempting to retrieve a random response')
        failed_conditions = []
        passed_conditions = {}
        successful_response = None

        for priority, responses in self._responses.items():
            self._log.debug('Attempting priority {priority} responses'.format(priority=priority))
            response_pool = []

            for response in responses:
                # If the response has a condition, attempt to evaluate it
                condition = self._conditionals[response] if response in self._conditionals else None
                if condition:
                    # Condition has already been evaluated and the evaluation failed, skip and continue
                    if condition in failed_conditions:
                        self._log.debug('Skipping response due to a previously failed condition check')
                        continue
                    # Condition has already been evaluated successfully, check if this response is in the cond. results
                    elif condition in passed_conditions:
                        if response in passed_conditions[condition]:
                            self._log.debug('Response is in a condition that has already been successfully evaluated')
                        else:
                            # This error is kinda ambiguous, but it basically means the condition evaluated true,
                            # but this specific response was in a different if / elif / else statement
                            self._log.debug('Response is in a condition that has already been successfully evaluated, '
                                            'but the response was in the wrong condition statement, skipping')
                            continue
                    # Condition has not been evaluated yet, process it now and save the result
                    elif condition not in passed_conditions:
                        self._log.debug('Evaluating a new condition')
                        evaluated = condition.evaluate(user)
                        # Fail, skip and continue
                        if not evaluated:
                            self._log.debug('Condition failed to evaluate successfully, skipping response')
                            failed_conditions.append(condition)
                            continue

                        # Pass
                        self._log.debug('Condition evaluated successfully, checking if we\'re in the right condition '
                                        'statement')
                        passed_conditions[condition] = evaluated

                        if response in passed_conditions[condition]:
                            self._log.debug('Response is in the successfully evaluated condition statement, continuing')
                        else:
                            # This error is kinda ambiguous, but it basically means the condition evaluated true,
                            # but this specific response was in a different if / elif / else statement
                            self._log.debug('Response was in the wrong condition statement, skipping')
                            continue

                # Does the user have a limit for this response enforced?
                if user and user.is_limited(response):
                    if response.ulimit_blocking:
                        self._log.debug('An active blocking limit for this response is being enforced against the user '
                                        '{uid}, no response will be returned'.format(uid=user.id))
                        raise LimitError

                    self._log.debug('An active limit for this response is being enforced against the user {uid}, '
                                    'skipping'.format(uid=user.id))
                    continue

                # Is there a global limit for this response enforced?
                if response.agentml.is_limited(response):
                    if response.glimit_blocking:
                        self._log.debug('An active blocking limit for this response is being enforced globally, no '
                                        'response will be returned')
                        raise LimitError

                    self._log.debug('An active limit for this response is being enforced globally, skipping')
                    continue

                self._log.debug('Adding new response to the random pool with a weight of {weight}'
                                .format(weight=response.weight))
                response_pool.append((response, response.weight))

            # If we have no responses in the response pool, that means a limit is being enforced for them all and
            # we need to move on to responses in the next priority bracket
            if not response_pool:
                self._log.debug('All responses with a priority of {priority} failed to pass one or more condition '
                                'checks, continuing to the next priority bracket'.format(priority=priority))
                continue

            # Start a loop so we can weed out responses that fail chance conditions
            while True:
                # Retrieve a random weighted response
                response = weighted_choice(response_pool)

                # Are we out of responses to try?
                if not response:
                    break

                # Is there a chance we need to evaluate?
                if response.chance is None or response.chance == 100:
                    successful_response = response
                    break

                # Chance succeeded
                if response.chance >= random.uniform(0, 100):
                    self._log.info('Response had a {chance}% chance of being selected and succeeded selection'
                                   .format(chance=response.chance))
                    successful_response = response
                    break
                # Chance failed
                else:
                    if response.chance_blocking:
                        self._log.info('Response had a blocking {chance}% chance of being selected but failed selection'
                                       ', no response will be returned'.format(chance=response.chance))
                        raise ChanceError

                    self._log.info('Response had a {chance}% chance of being selected but failed selection'
                                   .format(chance=response.chance))
                    response_pool = [r for r in response_pool if r[0] is not response]
                    continue

            # If we have no successful response defined, that means a chance condition for all the responses failed and
            # we need to move on to responses in the next priority bracket
            if successful_response is None:
                self._log.debug('All responses with a priority of {priority} have chance conditions defined and we '
                                'failed to pass any of them, continuing to the next priority bracket'
                                .format(priority=priority))
                continue

            # If we're still here, that means we DO have a successful response ans we should process it immediately
            if user:
                successful_response.apply_reactions(user)

            return successful_response

        # If we looped through everything but haven't returned yet, that means we ran out of responses to attempt
        self._log.info('All responses failed to pass one or more condition checks, nothing to return')
