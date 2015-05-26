class Tag:
    def __init__(self, trigger, element):
        self.trigger = trigger
        self._element = element

        # TODO: Optional schema validation
        self.schema = NotImplemented