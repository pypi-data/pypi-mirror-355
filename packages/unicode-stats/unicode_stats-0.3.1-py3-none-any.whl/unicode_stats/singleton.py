"""
    Be sure that
    Only 1 instance of unicode_parser at one process
"""


class SingletonClass(object):
    """A singleton class that ensures only one instance of the class exists."""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SingletonClass, cls).__new__(cls)
        return cls.instance
