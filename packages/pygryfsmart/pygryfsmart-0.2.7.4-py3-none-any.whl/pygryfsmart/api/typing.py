from .const import DriverFunctions

import logging

_LOGGER = logging.getLogger(__name__)

class GryfData(dict):
    _drivers = []

    _key_list = [
        DriverFunctions.OUTPUTS,
        DriverFunctions.INPUTS,
        DriverFunctions.PWM,
        DriverFunctions.FIND,
        DriverFunctions.PONG,
        DriverFunctions.TEMP,
        DriverFunctions.COVER,
    ]

    def __new__(cls):
        return super(GryfData, cls).__new__(cls)

    def __init__(self):
        super().__init__()
        for key in self._key_list:
            self[key] = {}

    def __repr__(self):
        return f"GryfData({dict.__repr__(self)})"

    def __getitem__(self, key):
        if key in self._key_list:
            return super().__getitem__(key)
        _LOGGER.error(f"Bad dict key: {key}")
        raise KeyError(f"Invalid key: {key}")

    def __setitem__(self, key, value):
        if key in self._key_list:
            return super().__setitem__(key, value)
        _LOGGER.error(f"Bad dict key: {key}")
        raise KeyError(f"Invalid key: {key}")

    def get(self, key, default=None):
        if key in self._key_list:
            return super().get(key, default)
        _LOGGER.error(f"Bad dict key in get(): {key}")
        return default

    def setdefault(self, key, default=None):
        if key in self._key_list:
            return super().setdefault(key, default)
        _LOGGER.error(f"Bad dict key in setdefault(): {key}")
        raise KeyError(f"Invalid key: {key}")

    def update(self, other=None, **kwargs):
        if other:
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]

    @property
    def inputs(self):
        return self[DriverFunctions.INPUTS]

    @property
    def outputs(self):
        return self[DriverFunctions.OUTPUTS]

    @property
    def pwms(self):
        return self[DriverFunctions.PWM]

    @property
    def finds(self):
        return self[DriverFunctions.FIND]

    @property
    def pongs(self):
        return self[DriverFunctions.PONG]

    @property
    def temps(self):
        return self[DriverFunctions.TEMP]

    @property
    def covers(self):
        return self[DriverFunctions.COVER]
