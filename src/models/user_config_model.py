from src.core.model import Model
from src.core.constants import DEFAULT_USER_CONFIG_FILE
from dataclasses import dataclass
import pickle
import logging
from PySide6.QtCore import Signal, QObject
from src.models.line_model import NavRoute

VERSION = (1, 0, 1)


@dataclass
class UserConfigData:
    """Serializable data that is saved locally and is used by UserConfigModel"""
    version: tuple
    favourite_complexes: dict
    favourite_routes: dict


class UserConfigModel(Model, QObject):
    """
    Model supports locally stored data, such as user preferences, settings and favourites.
    By default, loads/saves to DEFAULT_USER_CONFIG_FILE.
    """
    favourites_updated = Signal()
    groups_updated = Signal()
    favourite_routes_updated = Signal()
    groups_routes_updated = Signal()

    def __init__(self):
        super().__init__(None)
        self._data = UserConfigData(
            version=VERSION,
            favourite_complexes=dict(),
            favourite_routes=dict()
        )

    @staticmethod
    def get_instance():
        return _USER_CONFIG_MODEL_INSTANCE

    def add_favourite_complex(self, group: str, stop_complex_id: int, no_emit: bool = False):
        self._data.favourite_complexes[group].add(stop_complex_id)
        if not no_emit:
            self.favourites_updated.emit()

    def remove_favourite_complex(self, group: str, stop_complex_id: int, no_emit: bool = False):
        self._data.favourite_complexes[group].remove(stop_complex_id)
        if not no_emit:
            self.favourites_updated.emit()

    def remove_favourite_complexes(self, removal_list: list, no_emit: bool = False):
        for group, stop_complex in removal_list:
            if group in self._data.favourite_complexes:
                self._data.favourite_complexes[group].remove(stop_complex)
        if not no_emit:
            self.favourites_updated.emit()

    def add_new_group(self, group: str, no_emit: bool = False):
        if group == "":
            raise ValueError("Group name must have at least one character")
        self._data.favourite_complexes[group] = set()
        if not no_emit:
            self.groups_updated.emit()

    def rename_group(self, group_before, group_after):
        favs = self._data.favourite_complexes[group_before]
        self._data.favourite_complexes[group_after] = favs
        self._data.favourite_complexes.pop(group_before)

        self.groups_updated.emit()

    def remove_group(self, group: str, no_emit: bool = False):
        self._data.favourite_complexes.pop(group)
        if not no_emit:
            self.groups_updated.emit()

    def remove_groups(self, groups: list, no_emit: bool = False):
        for group in groups:
            self._data.favourite_complexes.pop(group)
        if not no_emit:
            self.groups_updated.emit()

    def get_favourite_complexes(self):
        """
        Returns a list of complex ids favourited by the user
        :return: list of stop_complex_id's
        """
        return self._data.favourite_complexes

    def get_favourites_by_group(self, group: str):
        return self._data.favourite_complexes[group]

    def get_groups(self):
        """
        :return: Returns a list of group names
        """
        return list(self._data.favourite_complexes.keys())


    
    """ Routes """

    def add_favourite_route(self, group: str, route: NavRoute, no_emit: bool = False):
        self._data.favourite_routes[group].add(route)
        if not no_emit:
            self.favourite_routes_updated.emit()

    def remove_favourite_route(self, group: str, route: NavRoute, no_emit: bool = False):
        self._data.favourite_routes[group].remove(route)
        if not no_emit:
            self.favourite_routes_updated.emit()

    def remove_favourite_routes(self, removal_list: list, no_emit: bool = False):
        for group, route in removal_list:
            if group in self._data.favourite_routes:
                self._data.favourite_routes[group].remove(route)
        if not no_emit:
            self.favourite_routes_updated.emit()

    def add_new_routes_group(self, group: str, no_emit: bool = False):
        if group == "":
            raise ValueError("Group name must have at least one character")
        self._data.favourite_routes[group] = set()
        if not no_emit:
            self.groups_routes_updated.emit()

    def rename_routes_group(self, group_before, group_after):
        favs = self._data.favourite_routes[group_before]
        self._data.favourite_routes[group_after] = favs
        self._data.favourite_routes.pop(group_before)

        self.groups_routes_updated.emit()

    def remove_routes_group(self, group: str, no_emit: bool = False):
        self._data.favourite_routes.pop(group)
        if not no_emit:
            self.groups_routes_updated.emit()

    def remove_routes_groups(self, groups: list, no_emit: bool = False):
        for group in groups:
            self._data.favourite_routes.pop(group)
        if not no_emit:
            self.groups_routes_updated.emit()

    def get_favourite_routes(self):
        return self._data.favourite_routes

    def get_favourites_routes_by_group(self, group: str):
        return self._data.favourite_routes[group]

    def get_routes_groups(self):
        return list(self._data.favourite_routes.keys())



    @property
    def version(self):
        return self._data.version

    def load(self, byte_stream=None, no_emit: bool = False):
        """
        Loads pickled user config. If not stream is provided, it uses the default file location defined in constants.
        :param no_emit: if true, data update signals wont be sent
        :param byte_stream: Optional stream to load the config from
        """
        stream = None
        if byte_stream is None:
            # Open default file location if stream not provided
            try:
                stream = open(DEFAULT_USER_CONFIG_FILE, "rb")
            except FileNotFoundError:
                logging.info("Config file missing. Creating a blank one.")
                # Create a blank and save it
                self.revert_to_defaults()
                return
            except PermissionError:
                logging.critical("No permission to read config!")
        else:
            stream = byte_stream

        unpickled_data = pickle.load(stream)
        if unpickled_data.version == self._data.version:
            self._data = unpickled_data
        else:
            logging.warning("Incompatible config version, reverting to defaults")
            self.revert_to_defaults()

        if byte_stream is None:
            stream.close()

        # Emit data update signals
        if not no_emit:
            self.favourites_updated.emit()

    def save(self, byte_stream=None):
        """
        Saves pickled user config. If not stream is provided, it uses the default file location defined in constants.
        :param byte_stream: Optional stream to save the config to
        """
        stream = None
        if byte_stream is None:
            # Open default file location if stream not provided
            try:
                stream = open(DEFAULT_USER_CONFIG_FILE, "wb")
            except PermissionError:
                logging.critical("No permission to save config file!")
                return
        else:
            stream = byte_stream

        pickle.dump(self._data, stream)

        if byte_stream is None:
            stream.close()

    def has_changed(self):
        some_new = UserConfigModel()
        some_new.load()

        return not some_new == self

    def __eq__(self, other):
        # That shit wasn't easy...

        keys1, values1 = [], []
        for key, value in other._data.favourite_routes.items():
            keys1.append(key)
            for v in value:
                values1.append((v.start_stop_id, v.destination_stop_id))

        keys2, values2 = [], []
        for key, value in self._data.favourite_routes.items():
            keys2.append(key)
            for v in value:
                values2.append((v.start_stop_id, v.destination_stop_id))
        values1 = sorted(values1)
        values2 = sorted(values2)
        return keys2 == keys1 and values2 == values1 and \
        other._data.favourite_complexes == self._data.favourite_complexes and \
        other._data.version == self._data.version


    def revert_to_defaults(self):
        temp = UserConfigModel()
        temp.save()
        del temp
        self.load()


_USER_CONFIG_MODEL_INSTANCE = UserConfigModel()
