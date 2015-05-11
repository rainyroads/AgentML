from parser import Element


class Response(Element):
    def __init__(self, saml, element, file_path):
        super().__init__(saml, element, file_path)
        self._response = []
        self.tags = {}

    def _parse_response(self):
        # If the response element has no tags, just store the raw text as the only response
        if len(self._element) == 1:
            self._response.append(self._element.text)
            return

        # Add the starting text to the response list
        head = self._element.text.strip() if isinstance(self._element.text, str) else None
        if head:
            self._response.append(head)

        # Parse the contained tags and add their associated string objects to the response list
        for child in self._element:
            # Make sure a parser for this tag exists
            if child.tag not in self.tags:
                continue

            # Append the tag object to the response string
            tag = self.tags[child.tag]
            self._response.append(tag(self.saml, child))

            # Append the trailing text to the response string (if there is any)
            tail = child.tail.strip() if isinstance(child.tag, str) else None
            if tail:
                self._response.append(tail)

    def __str__(self):
        return ''.join(self._response)