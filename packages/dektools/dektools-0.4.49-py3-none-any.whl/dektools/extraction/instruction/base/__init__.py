import functools


class InstructionBase:
    head = ''

    def __init__(self, instruction_set, key, value):
        self.instruction_set = instruction_set
        self.key_raw = key
        self.value = value

    @classmethod
    def recognize(cls, key):
        return cls.head == '' or key.startswith(cls.head)

    @functools.cached_property
    def key(self):
        return self.key_raw[len(self.head):].strip()
