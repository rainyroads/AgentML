import logging
from parser import Element


class Response(Element):
    def __init__(self, saml, element, file_path):
        self._response = []

        self._log = logging.getLogger('saml.parser.trigger.response')
        super().__init__(saml, element, file_path)

    def _parse(self):
        # If the response element has no tags, just store the raw text as the only response
        if not len(self._element):
            self._response.append(self._element.text)
            self._log.info('Assigning text only response')
            return

        # Add the starting text to the response list
        head = self._element.text if isinstance(self._element.text, str) else None
        if head:
            self._log.debug('Appending heading text')
            self._response.append(head)

        # Parse the contained tags and add their associated string objects to the response list
        for child in self._element:
            # Make sure a parser for this tag exists
            if child.tag not in self.saml.tags:
                self._log.warn('No parse available for tag "{tag}", skipping'.format(tag=child.tag))
                continue

            # Append the tag object to the response string
            tag = self.saml.tags[child.tag]
            self._log.debug('Appending tag object')
            self._response.append(tag(self.saml, child))

            # Append the trailing text to the response string (if there is any)
            tail = child.tail if isinstance(child.tail, str) else None
            if tail:
                self._log.debug('Appending trailing text')
                self._response.append(tail)

    def __str__(self):
        self._log.debug('Converting Response object to string form')
        return ''.join(map(str, self._response)).strip()
