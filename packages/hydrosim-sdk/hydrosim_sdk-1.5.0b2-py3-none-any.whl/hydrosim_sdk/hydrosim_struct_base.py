import ctypes
import json
from uuid import UUID
from dtypes.structify import structify

from hydrosim_sdk.ctypes_json import CDataJSONEncoder


class HydroSimStructure(ctypes.Structure):
    _pack_ = 1

    def __iter__(self):
        for prop in self.__properties__:
            val = getattr(self, prop)
            if isinstance(val, HydroSimStructure):
                yield prop, dict(getattr(self, prop))
            else:
                yield prop, getattr(self, prop)

    def to_json(self, indent=None):
        return json.dumps(self, cls=CDataJSONEncoder, indent=indent)

    def __repr__(self):
        return self.to_json(indent=2)


def hydrosimify(cls):
    new_annotations = {}
    properties = []
    for data in cls.__annotations__.items():
        name = data[0]
        rest = data[1]
        enum_type = None
        arr_count = None
        if isinstance(rest, tuple):
            if len(rest) == 3:
                arr_count = rest[2]
                rest = rest[0]
            elif len(rest) > 1:
                enum_type = rest[1]
                rest = rest[0]

        properties.append(name)

        if not name.startswith("__") and not name.startswith("_"):
            under_name = f"_{name}"

            if "c_char" in rest.__name__ and "Array" in rest.__name__:

                def str_getter(self, under_name=under_name):
                    return str(getattr(self, under_name), encoding="utf-8")

                def str_setter(self, val, under_name=under_name):
                    setattr(self, under_name, bytes(val, encoding="utf-8"))

                setattr(cls, name, property(str_getter, str_setter))
                name = under_name

            elif rest == ctypes.c_ubyte * 16:

                def uuid_getter(self, under_name=under_name):
                    return UUID(bytes=bytes(getattr(self, under_name)))

                def uuid_setter(self, val: UUID, under_name=under_name):
                    setattr(self, under_name, val.bytes)

                setattr(cls, name, property(uuid_getter, uuid_setter))
                name = under_name

            elif "Array" in rest.__name__:

                def array_getter(self, under_name=under_name):
                    arr = getattr(self, under_name)
                    count_field = f"{under_name}Count"
                    if arr_count:
                        count_field = arr_count
                    count = getattr(self, count_field)
                    return [arr[i] for i in range(count)]

                setattr(cls, name, property(array_getter))
                name = under_name

            elif enum_type:

                def enum_getter(self, under_name=under_name, enum_type=enum_type):
                    return enum_type(getattr(self, under_name))

                def enum_setter(self, val, under_name=under_name, rest=rest):
                    setattr(self, under_name, rest(val))

                setattr(cls, name, property(enum_getter, enum_setter))
                name = under_name

            elif rest == ctypes.c_int or rest == ctypes.c_uint:

                def int_getter(self, under_name=under_name):
                    return int(getattr(self, under_name))

                ctype = ctypes.c_int
                if rest == ctypes.c_uint:
                    ctype = ctypes.c_uint

                def int_setter(self, val, under_name=under_name, ctype=ctype):
                    setattr(self, under_name, ctype(val))

                setattr(cls, name, property(int_getter, int_setter))
                name = under_name

            elif rest == ctypes.c_float or rest == ctypes.c_double:

                def float_getter(self, under_name=under_name):
                    return float(getattr(self, under_name))

                ctype = ctypes.c_double
                if rest == ctypes.c_float:
                    ctype = ctypes.c_float

                def float_setter(self, val, under_name=under_name, ctype=ctype):
                    setattr(self, under_name, ctype(val))

                setattr(cls, name, property(float_getter, float_setter))
                name = under_name

            elif rest == ctypes.c_bool:

                def bool_getter(self, under_name=under_name):
                    return bool(getattr(self, under_name))

                def bool_setter(self, val, under_name=under_name):
                    setattr(self, under_name, ctypes.c_bool(val))

                setattr(cls, name, property(bool_getter, bool_setter))
                name = under_name

            new_annotations[name] = rest

    cls.__annotations__ = new_annotations
    cls.__properties__ = properties

    return structify(cls)
