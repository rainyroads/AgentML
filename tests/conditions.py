from agentml.parser.trigger.condition.types import ConditionType


class FooBarType(ConditionType):
    """
    Takes the key "foo" and returns "bar", or "bar" and returns "foo"
    """
    # def __init__(self):
    #     super().__init__('foo_bar')

    def get(self, agentml, user=None, key=None):
        if key == 'foo':
            return 'bar'

        if key == 'bar':
            return 'foo'
