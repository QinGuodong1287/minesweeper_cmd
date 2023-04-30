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
        """
        try:
            raise Exception
        except:
            import os, traceback
            if not os.path.exists(r"varlog.log"):
                with open(r"varlog.log", "w") as fp:
                    pass
            with open(r"varlog.log", "a") as fp:
                traceback.print_exc(file=fp)
                fp.write(str(type(self.value)) + ' ' + str(self.value))
                fp.write('\n\n')
        """

    def get(self):
        return self.value

    def __getattr__(self, name):
        return getattr(self.value, name)
