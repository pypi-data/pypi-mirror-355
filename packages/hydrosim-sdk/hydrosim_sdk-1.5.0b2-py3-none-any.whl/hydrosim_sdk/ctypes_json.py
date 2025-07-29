# -*- coding: utf-8 -*-

from ctypes import Array, Structure, Union, _Pointer, _SimpleCData
from json import JSONEncoder
from uuid import UUID

__version__ = "1.0.0"


class CDataJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (Array, list)):
            return [self.default(e) for e in obj]

        if isinstance(obj, _Pointer):
            return self.default(obj.contents) if obj else None

        if isinstance(obj, _SimpleCData):
            return self.default(obj.value)

        if isinstance(obj, (bool, int, float, str)):
            return obj

        if obj is None:
            return obj

        if isinstance(obj, (Structure, Union)):
            result = {}
            anonymous = getattr(obj, "_anonymous_", [])

            for key, *_ in getattr(obj, "_fields_", []):
                value = getattr(obj, key)

                # private fields don't encode
                if key.startswith("_"):
                    if hasattr(obj, key[1:]):
                        key = key[1:]
                        value = getattr(obj, key)
                    else:
                        continue

                if key in anonymous:
                    result.update(self.default(value))
                else:
                    result[key] = self.default(value)

            return result

        if isinstance(obj, UUID):
            return str(obj)

        if isinstance(obj, bytes):
            return str(obj, encoding="utf-8")

        return JSONEncoder.default(self, obj)
