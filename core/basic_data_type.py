class LimitedVar:
    def __init__(self, value=None, min_value=None, max_value=None):
        self.value = value
        if min_value is not None and max_value is not None and min_value > \
                max_value:
            max_value = min_value
        self.__min_value = min_value
        self.__max_value = max_value
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

    def get(self):
        return self.value

    def __getattr__(self, name):
        return getattr(self.value, name)

    @property
    def min_value(self):
        return self.__min_value

    @min_value.setter
    def min_value(self, min_value):
        self.__min_value = min_value
        self.__correct_value()

    @min_value.deleter
    def min_value(self):
        del self.__min_value
        self.__min_value = None
        self.__correct_value()

    @property
    def max_value(self):
        return self.__max_value

    @max_value.setter
    def max_value(self, max_value):
        self.__max_value = max_value
        self.__correct_value()

    @max_value.deleter
    def max_value(self):
        del self.__max_value
        self.__max_value = None
        self.__correct_value()
