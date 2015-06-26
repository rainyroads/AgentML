from time import sleep
from .config import AgentMLTestCase


class BasicResponseTests(AgentMLTestCase):
    """
    Basic response testing
    """
    def test_atomic(self):
        self.get_reply('atomic test', self.success)
        self.get_reply('ATOMIC test', self.success)
        self.get_reply('AtOm!ic test', self.success)
        self.get_reply('atomic. test.', self.success)
        self.get_reply('Atomic.. test!', self.success)
        self.get_reply('A!T!O!M!I!C T!E!S!T', self.success)

    def test_substitution(self):
        self.get_reply('atom test', self.success)
        self.get_reply('ATOM test', self.success)
        self.get_reply('AtOm! test', self.success)
        self.get_reply('atom. test.', self.success)
        self.get_reply('Atom.. test!', self.success)
        self.get_reply('A!T!O!M! T!E!S!T!', self.success)

    def test_optionals(self):
        self.get_reply('optional test 1', self.success)
        self.get_reply('optional foo test 1', self.success)
        self.get_reply('optional FOO test 1', self.success)
        self.get_reply('optional bar test 1', self.success)
        self.get_reply('optional, bar, test 1', self.success)
        self.get_reply('optional foo bar test 1', None)
        self.get_reply('optional foobar test 1', None)
        self.get_reply('optional test 2', self.success)
        self.get_reply('foo optional test 2', self.success)
        self.get_reply('optional test 3', self.success)
        self.get_reply('foo optional test 3', self.success)
        self.get_reply('foo optional test 3 bar', self.success)
        self.get_reply('optional test 3 bar', self.success)
        self.get_reply('optional test 3 foo', None)

    def test_required(self):
        self.get_reply('required test', None)
        self.get_reply('required foo test', 'foo')
        self.get_reply('required bar test', 'bar')
        self.get_reply('foo required test foo', None)

    def test_response_shorthand(self):
        self.get_reply('shorthand response test', self.success)

    def test_response_shorthand_with_condition(self):
        self.get_reply('shorthand conditional response test', self.failure)

        self.get_reply('Set user var condition to foo', 'Setting user variable condition to foo')
        self.user_var('condition', 'foo')

        self.get_reply('shorthand conditional response test', self.success)

    def test_wildcard(self):
        self.get_reply('wildcard test foo', 'foo')

    def test_empty_wildcard(self):
        self.get_reply('wildcard test', None)

    def test_alpha_wildcard_with_alpha(self):
        self.get_reply('alpha wildcard test foo', 'foo')

    def test_alpha_wildcard_with_numeric(self):
        self.get_reply('alpha wildcard test 42', None)

    def test_empty_alpha_wildcard(self):
        self.get_reply('alpha wildcard test', None)

    def test_numeric_wildcard_with_numeric(self):
        self.get_reply('numeric wildcard test 42', '42')

    def test_numeric_wildcard_with_alpha(self):
        self.get_reply('numeric wildcard test foo', None)

    def test_empty_numeric_wildcard(self):
        self.get_reply('numeric wildcard test', None)

    def test_discarded_wildcard(self):
        self.get_reply('discarded foo wildcard test bar', 'bar')

    def test_empty_discarded_wildcard(self):
        self.get_reply('discarded wildcard test foo', None)


class StarFormattingTests(AgentMLTestCase):
    """
    Wildcard / star format testing
    """
    def test_capitalize(self):
        self.get_reply('capitalize format foo, BAR, baZ, qUx', 'Foo bar baz qux')

    def test_title(self):
        self.get_reply('title format foo, BAR, baZ, qUx', 'Foo Bar Baz Qux')

    def test_upper(self):
        self.get_reply('upper format foo, BAR, baZ, qUx', 'FOO BAR BAZ QUX')

    def test_case_preserved(self):
        self.get_reply('case preserved format foo, BAR, baZ, qUx', 'foo BAR baZ qUx')

    def test_raw(self):
        self.get_reply('raw format foo, BAR, baZ, qUx', 'foo, BAR, baZ, qUx')


class TriggerLimitTests(AgentMLTestCase):
    def test_global_limit(self):
        self.get_reply('global limit test', self.success)
        self.get_reply('global limit test', None)

        self.username = 'limit_test'
        self.get_reply('global limit test', None)

        self.username = 'unittest'
        self.get_reply('global limit test', None)

        sleep(1)

        self.get_reply('global limit test', self.success)

    def test_user_limit(self):
        self.get_reply('user limit test', self.success)
        self.get_reply('user limit test', None)

        self.username = 'limit_test'

        self.get_reply('user limit test', self.success)
        self.get_reply('user limit test', None)

        sleep(1)

        self.get_reply('user limit test', self.success)
        self.username = 'unittest'
        self.get_reply('user limit test', self.success)


class ResponseLimitTests(AgentMLTestCase):
    def test_global_limit(self):
        self.get_reply('global response limit test', 'First!')
        self.get_reply('global response limit test', self.success)

        self.username = 'limit_test'
        self.get_reply('global response limit test', self.success)

        self.username = 'unittest'
        self.get_reply('global response limit test', self.success)

        sleep(1)

        self.get_reply('global response limit test', 'First!')
        self.get_reply('global response limit test', self.success)

        self.username = 'limit_test'
        self.get_reply('global response limit test', self.success)

        self.username = 'unittest'
        self.get_reply('global response limit test', self.success)

    def test_user_limit(self):
        self.get_reply('user response limit test', 'First!')
        self.username = 'limit_test'
        self.get_reply('user response limit test', 'First!')

        self.get_reply('user response limit test', self.success)
        self.username = 'unittest'
        self.get_reply('user response limit test', self.success)

        sleep(1)

        self.get_reply('user response limit test', 'First!')
        self.username = 'limit_test'
        self.get_reply('user response limit test', 'First!')

        self.get_reply('user response limit test', self.success)
        self.username = 'unittest'
        self.get_reply('user response limit test', self.success)


class ChanceTests(AgentMLTestCase):
    def test_response_chance(self):
        self.chance('response chance')

    def test_trigger_chance(self):
        self.chance('trigger chance')


class VarTests(AgentMLTestCase):
    def test_get_user_var(self):
        self.aml.get_user(self.username)
        self.aml.set_var('unittest', self.success, self.username)
        self.user_var('unittest', self.success)
        self.get_reply('Get user var unittest', self.success)

        self.username = 'var_test'
        self.aml.get_user(self.username)
        self.user_var('unittest', None)
        self.get_reply('Get user var unittest', '')

    def test_get_global_var(self):
        self.aml.set_var('unittest', self.success)
        self.global_var('unittest', self.success)
        self.get_reply('Get global var unittest', self.success)

        self.username = 'var_test'
        self.global_var('unittest', self.success)
        self.get_reply('Get global var unittest', self.success)

    def test_set_user_var(self):
        self.get_reply('Set user var unittest to {expected}'.format(expected=self.success),
                       'Setting user variable unittest to {expected}'.format(expected=self.success))
        self.user_var('unittest', self.success)

    def test_set_global_var(self):
        self.get_reply('Set global var unittest to {expected}'.format(expected=self.success),
                       'Setting global variable unittest to {expected}'.format(expected=self.success))
        self.global_var('unittest', self.success)


class ConditionTests(AgentMLTestCase):
    def test_condition(self):
        self.get_reply('condition test 1', self.failure)
        self.get_reply('condition test 2', self.failure)
        self.get_reply('condition test 3', None)
        self.get_reply('condition test 4', 'The condition variable has not been set!')

        self.get_reply('Set user var condition to foo', 'Setting user variable condition to foo')
        self.user_var('condition', 'foo')

        self.get_reply('condition test 1', self.success)
        self.get_reply('condition test 2', 'Success! Var is foo')
        self.get_reply('condition test 3', None)
        self.get_reply('condition test 4', 'The value of the condition variable is "foo"')

        self.get_reply('Set user var condition to bar', 'Setting user variable condition to bar')
        self.user_var('condition', 'bar')

        self.get_reply('condition test 1', self.success)
        self.get_reply('condition test 2', 'Success! Var is bar')
        self.get_reply('condition test 3', None)
        self.get_reply('condition test 4', 'The value of the condition variable is "bar"')

        self.get_reply('Set user var condition to baz', 'Setting user variable condition to baz')
        self.user_var('condition', 'baz')

        self.get_reply('condition test 1', self.success)
        self.get_reply('condition test 2', self.failure)
        self.get_reply('condition test 3', None)
        self.get_reply('condition test 4', 'The value of the condition variable is "baz"')

        self.get_reply('Set user var condition to 5', 'Setting user variable condition to 5')
        self.user_var('condition', '5')

        self.get_reply('condition test 1', self.success)
        self.get_reply('condition test 2', self.failure)
        self.get_reply('condition test 3', 'Success! Var is less than or equal to 10')
        self.get_reply('condition test 4', 'The value of the condition variable is "5"')

        self.get_reply('Set user var condition to 50', 'Setting user variable condition to 50')
        self.user_var('condition', '50')

        self.get_reply('condition test 1', self.success)
        self.get_reply('condition test 2', self.failure)
        self.get_reply('condition test 3', None)
        self.get_reply('condition test 4', 'The value of the condition variable is "50"')


class TopicTests(AgentMLTestCase):
    def test_enter_and_exit_topic(self):
        self.get_reply('enter test topic', self.success)
        self.topic('test')
        self.get_reply('test topic test', self.success)

        self.get_reply('exit test topic', self.success)
        self.topic(None)
        self.get_reply('test topic test', None)

    def test_exit_topic_on_no_reply(self):
        self.get_reply('enter test topic', self.success)
        self.topic('test')

        self.get_reply('atomic test', self.success)
        self.topic(None)


class GroupTests(AgentMLTestCase):
    def test_public_group(self):
        self.get_reply('public group test', self.success, {'public'})
        self.get_reply('public group test', None)

    def test_multiple_groups(self):
        self.get_reply('multigroup test', self.success, {'group1', 'group2', 'group3'})
        self.get_reply('multigroup test', None, {'group1', 'group2'})
        self.get_reply('multigroup test', None, {'group1', 'group3'})
        self.get_reply('multigroup test', None, {'group2'})
        self.get_reply('multigroup test', None)

    def test_multiple_groups_with_topic(self):
        self.get_reply('enter test topic', self.success)
        self.topic('test')

        self.get_reply('test topic group test', self.success, {'group1', 'group2'})
        self.topic('test')

        self.get_reply('test topic group test', None)
        self.topic(None)


class PriorityTests(AgentMLTestCase):
    def test_atomic_priority(self):
        self.get_reply('priority test', self.success)

    def test_response_priority(self):
        self.get_reply('response priority test', 'One')
        self.get_reply('response priority test', 'Two')
        self.get_reply('response priority test', 'Three')
        self.get_reply('response priority test', 'If you saw One, Two, Three before this message, this was a success!')

    def test_response_priority_with_condition(self):
        self.username = 'chell'
        self.get_reply('response priority test', 'One')
        self.get_reply('response priority test', 'Two')
        self.get_reply('response priority test', 'Three')
        self.get_reply('response priority test', 'If you saw One, Two, Three before this message, this was a triumph!')


class BlockingTests(AgentMLTestCase):
    def test_trigger_blocking(self):
        self.get_reply('blocking test', 'First!')
        self.get_reply('blocking test', self.success)

    def test_response_blocking(self):
        self.get_reply('response blocking test', 'First!')
        self.get_reply('response blocking test', self.success)
