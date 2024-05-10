from src.core.database import Database


class Model:
    """
    Base class for all abstract models
    """
    pass


class DBModel(Model):
    """
    Base class for Database dependent models
    """

    def __init__(self):
        self._db = Database()
