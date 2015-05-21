import os
import logging
from parser import Element, attribute, int_attribute
from parser.common import schema


class Response(Element):
    def __init__(self, trigger, element, file_path):
        self.trigger = trigger
        self._response = []

        with open(os.path.join(self.trigger.saml.script_path, 'schemas', 'tags', 'star.rng')) as file:
            self.schema = schema(file.read())

        self._log = logging.getLogger('saml.parser.trigger.response')
        super().__init__(trigger.saml, element, file_path)

    def _parse(self):
        # If the response element has no tags, just store the raw text as the only response
        if not len(self._element):
            self._response.append(self._element.text)
            self._log.info('Assigning text only response')
            return

        # Add the starting text to the response list
        head = self._element.text if isinstance(self._element.text, str) else None
        if head:
            self._log.debug('Appending heading text: {text}'.format(text=head))
            self._response.append(head)

        # Parse the contained tags and add their associated string objects to the response list
        for child in self._element:
            # Parse star tags internally
            if child.tag == 'star':
                star_index = int_attribute(child, 'index', 1)
                star_format = attribute(child, 'format', 'none')
                self._log.debug('Appending Star tag object with index {no}'.format(no=star_index))

                self._response.append(Star(self.trigger, star_index, star_format))
                continue

            # Make sure a parser for this tag exists
            if child.tag not in self.saml.tags:
                self._log.warn('No parsers available for Tag "{tag}", skipping'.format(tag=child.tag))
                continue

            # Append the tag object to the response string
            tag = self.saml.tags[child.tag]
            self._log.debug('Appending {tag} Tag object'.format(tag=child.tag.capitalize()))
            self._response.append(tag(self.saml, child))

            # Append the trailing text to the response string (if there is any)
            tail = child.tail if isinstance(child.tail, str) else None
            if tail:
                self._log.debug('Appending trailing text: {text}'.format(text=tail))
                self._response.append(tail)

    def __str__(self):
        self._log.debug('Converting Response object to string format')
        return ''.join(map(str, self._response)).strip()


class Star:
    def __init__(self, trigger, index=1, star_format='none'):
        self.trigger = trigger
        self.index = index
        self.format = star_format
        self._log = logging.getLogger('saml.parser.trigger.star')

    def __str__(self):
        try:
            star = str(self.trigger.stars[self.index - 1])
        except IndexError:
            self._log.warn('No wildcard with the index {index} exists for this response'.format(index=self.index))
            return ''

        if self.format in ['title', 'upper', 'lower']:
            self._log.debug('Formatting wildcard as {format}'.format(format=self.format))
            star = getattr(star, self.format)()

        return star
