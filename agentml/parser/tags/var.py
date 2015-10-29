import os
import logging
from agentml.common import schema, attribute
from agentml.parser.tags import Tag
from agentml.errors import VarNotDefinedError


class Var(Tag):
    def __init__(self, trigger, element):
        """
        Initialize a new Random Tag instance
        :param trigger: The executing Trigger instance
        :type  trigger: parser.trigger.Trigger

        :param element: The XML Element object
        :type  element: etree._Element
        """
        super(Var, self).__init__(trigger, element)
        self._log = logging.getLogger('agentml.parser.tags.var')

        # Define our schema
        with open(os.path.join(self.trigger.agentml.script_path, 'schemas', 'tags', 'var.rng')) as file:
            self.schema = schema(file.read())

        # Is this a User or Global variable?
        self.type = attribute(element, 'type', 'user')

    def value(self):
        """
        Return the current value of a variable
        """
        # Does the variable name have tags to parse?
        if len(self._element):
            var = ''.join(map(str, self.trigger.agentml.parse_tags(self._element, self.trigger)))
        else:
            var = self._element.text or attribute(self._element, 'name')

        # Is there a default value defined?
        default = attribute(self._element, 'default')

        try:
            self._log.debug('Retrieving {type} variable {var}'.format(type=self.type, var=var))
            if self.type == 'user':
                return self.trigger.user.get_var(var)
            else:
                return self.trigger.agentml.get_var(var)
        except VarNotDefinedError:
            # Do we have a default value?
            if default:
                self._log.info('{type} variable {var} not set, returning default: {default}'
                               .format(type=self.type.capitalize(), var=var, default=default))

            self._log.info('{type} variable {var} not set and no default value has been specified'
                           .format(type=self.type.capitalize(), var=var))
            return ''
