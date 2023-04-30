class LimitedVar:
    def __init__(self, value=None, min_value=None, max_value=None):
        self.value = value
        if min_value is not None and max_value is not None and min_value > max_value:
            max_value = min_value
        self.min_value = min_value
        self.max_value = max_value
        self.__correct_value()

    def __correct_value(self):
        if self.value is None:
            return
        if self.max_value is not None:
            self.value = min(self.value, self.max_value)
        if self.min_value is not None:
            self.value = max(self.value, self.min_value)

    def set(self, new_value=None):
        self.value = new_value
        self.__correct_value()

    def __getattr__(self, name):
        return getattr(self.value, name)
