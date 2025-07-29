# copyright 2004-2025 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact https://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of yams.
#
# yams is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# yams is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with yams. If not, see <https://www.gnu.org/licenses/>.
"""Some common constraint classes."""

import re
import decimal
import operator
import json
import datetime
from dateutil.parser import parse

from typing import (
    Any,
    Dict,
    Match,
    Tuple,
    Type,
    Union,
    Optional,
    Callable,
    Sequence,
    List,
    cast,
)

from logilab.common.date import todate, todatetime
from typing_extensions import Literal

import yams
from yams import KEYWORD_MAP, BadSchemaDefinition
from yams.interfaces import IConstraint, IVocabularyConstraint
import yams.types as yams_types

__docformat__: str = "restructuredtext en"

_: Type[str] = str


class ConstraintJSONEncoder(json.JSONEncoder):
    def default(self, obj: Union[Any, "NOW", "TODAY"]) -> Union[Any, dict]:
        if isinstance(obj, Attribute):
            return {"__attribute__": obj.attr}

        if isinstance(obj, NOW):
            # it is not a timedelta
            if obj.offset is None:
                return {"__now__": True, "offset": obj.offset, "type": obj.type}

            d = {
                "days": obj.offset.days,
                "seconds": obj.offset.seconds,
                "microseconds": obj.offset.microseconds,
            }

            return {"__now__": True, "offset": d, "type": obj.type}

        if isinstance(obj, TODAY):
            # it is not a timedelta
            if obj.offset is None:
                return {"__today__": True, "offset": obj.offset, "type": obj.type}

            d = {
                "days": obj.offset.days,
                "seconds": obj.offset.seconds,
                "microseconds": obj.offset.microseconds,
            }

            return {"__today__": True, "offset": d, "type": obj.type}

        if isinstance(obj, (datetime.date, datetime.time, datetime.datetime)):
            return obj.isoformat()

        return super().default(obj)


def _json_object_hook(dct: Dict) -> Union[Dict, "NOW", "TODAY", "Attribute"]:
    offset: Optional[datetime.timedelta]

    if "__attribute__" in dct:
        return Attribute(dct["__attribute__"])

    if "__now__" in dct:
        if dct["offset"] is not None:
            offset = datetime.timedelta(**dct["offset"])
        else:
            offset = None

        return NOW(offset, type=dct.get("type", "TZDatetime"))

    if "__today__" in dct:
        if dct["offset"] is not None:
            offset = datetime.timedelta(**dct["offset"])
        else:
            offset = None

        return TODAY(offset=offset, type=dct["type"])

    return dct


def cstr_json_dumps(obj: yams_types.jsonSerializable) -> str:
    return str(ConstraintJSONEncoder(sort_keys=True).encode(obj))


cstr_json_loads: Callable[[str], Dict] = json.JSONDecoder(object_hook=_json_object_hook).decode


def _message_value(boundary) -> Any:
    if isinstance(boundary, Attribute):
        return boundary.attr
    elif isinstance(boundary, (NOW, TODAY)):
        return str(boundary)
    return boundary


class BaseConstraint:
    """base class for constraints"""

    __implements__ = IConstraint

    msg: Optional[str]
    """user defined message returned by failed_message when the constraint check fails"""

    def __init__(self, msg: Optional[str] = None) -> None:
        self.msg = msg

    def check_consistency(
        self,
        subjschema: yams_types.EntitySchema,
        objschema: yams_types.EntitySchema,
        rdef: yams_types.RelationDefinition,
    ) -> None:
        pass

    def type(self) -> str:
        return self.__class__.__name__

    def serialize(self) -> str:
        """called to make persistent valuable data of a constraint"""
        return cstr_json_dumps({"msg": self.msg})

    @classmethod
    def deserialize(cls: Type["BaseConstraint"], value: str) -> Any:
        """called to restore serialized data of a constraint. Should return
        a `cls` instance
        """
        value = value.strip()

        if value and value != "None":
            d = cstr_json_loads(value)
        else:
            d = {}

        return cls(**d)

    def failed_message(self, key: str, value, entity) -> Tuple[str, Dict[str, Any]]:
        if entity is None:
            raise ValueError("entity can't be None")

        if self.msg:
            return self.msg, {}

        return self._failed_message(entity, key, value)

    def _failed_message(self, entity, key: str, value) -> Tuple[str, Dict[str, Any]]:
        return (
            _("%(KEY-cstr)s constraint failed for value %(KEY-value)r"),
            {key + "-cstr": self, key + "-value": value},
        )

    def __eq__(self, other: Any) -> bool:
        return (self.type(), self.serialize()) == (other.type(), other.serialize())

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __lt__(self, other: Any) -> bool:
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.type(), self.serialize()))


# possible constraints ########################################################


class UniqueConstraint(BaseConstraint):
    """object of relation must be unique"""

    def __str__(self) -> str:
        return "unique"

    def check_consistency(
        self,
        subjschema: yams_types.EntitySchema,
        objschema: yams_types.EntitySchema,
        rdef: yams_types.RelationDefinition,
    ) -> None:
        if not objschema.final:
            raise BadSchemaDefinition("unique constraint doesn't apply to non " "final entity type")

    def check(self, entity, rtype: yams_types.RelationType, values) -> bool:
        """return true if the value satisfy the constraint, else false"""
        return True


def _len(value) -> int:
    try:
        return len(value)
    except TypeError:
        return len(value.getbuffer())


class SizeConstraint(BaseConstraint):
    """the string size constraint :

    if min is not None the string length must not be shorter than min
    if max is not None the string length must not be greater than max
    """

    def __init__(
        self, *, min: Optional[int] = None, max: Optional[int] = None, msg: Optional[str] = None
    ) -> None:
        super().__init__(msg)

        assert max is not None or min is not None, "No max or min"

        if min is not None:
            assert isinstance(min, int), f"min must be an int, not {min!r}"
            assert min >= 0

        if max is not None:
            assert isinstance(max, int), f"max must be an int, not {max!r}"
            assert max >= 0

        assert min is None or max is None or min <= max
        self.min: Optional[int] = min
        self.max: Optional[int] = max

    def __str__(self) -> str:
        res = "size"

        if self.max is not None:
            res = f"{res} <= {self.max}"

        if self.min is not None:
            res = f"{self.min} <= {res}"

        return res

    def check_consistency(
        self,
        subjschema: yams_types.EntitySchema,
        objschema: yams_types.EntitySchema,
        rdef: yams_types.RelationDefinition,
    ) -> None:
        if not objschema.final:
            raise BadSchemaDefinition("size constraint doesn't apply to non " "final entity type")

        if objschema not in ("String", "Bytes", "Password"):
            raise BadSchemaDefinition(f"size constraint doesn't apply to {objschema} entity type")

        if self.max:
            for cstr in rdef.constraints:
                if type(cstr) is StaticVocabularyConstraint:
                    for value in cstr.values:
                        if _len(value) > self.max:
                            raise BadSchemaDefinition(
                                "size constraint set to %s but vocabulary "
                                "contains string of greater size" % self.max
                            )

    def check(self, entity, rtype: yams_types.RelationType, value: Sequence) -> bool:
        """return true if the value is in the interval specified by
        self.min and self.max
        """

        value_length = _len(value)

        if self.max is not None and value_length > self.max:
            return False

        if self.min is not None and value_length < self.min:
            return False

        return True

    def _failed_message(self, entity, key: str, value: Sequence) -> Tuple[str, Dict[str, Any]]:
        value_length = _len(value)

        if self.max is not None and value_length > self.max:
            return (
                _("value should have maximum size of %(KEY-max)s" " but found %(KEY-size)s"),
                {key + "-max": self.max, key + "-size": value_length},
            )

        if self.min is not None and value_length < self.min:
            return (
                _("value should have minimum size of %(KEY-min)s" " but found %(KEY-size)s"),
                {key + "-min": self.min, key + "-size": value_length},
            )

        assert False, "shouldnt be there"

    def serialize(self) -> str:
        """simple text serialization"""
        return cstr_json_dumps({"min": self.min, "max": self.max, "msg": self.msg})

    @classmethod
    def deserialize(cls: Type["SizeConstraint"], value: str) -> "SizeConstraint":
        """simple text deserialization"""
        try:
            d = cstr_json_loads(value)

            return cls(**d)
        except ValueError:
            kwargs = {}

            for adef in value.split(","):
                key, val = [w.strip() for w in adef.split("=")]

                assert key in ("min", "max")

                kwargs[str(key)] = int(val)

            # mypy: Argument 1 to "SizeConstraint" has incompatible type "**Dict[str, int]";
            # mypy: expected "Optional[str]"
            # mypy seems really broken with **kwargs
            return cls(**kwargs)  # type: ignore


class RegexpConstraint(BaseConstraint):
    """specifies a set of allowed patterns for a string value"""

    __implements__ = IConstraint

    def __init__(self, regexp: str, flags: int = 0, msg: Optional[str] = None) -> None:
        """
        Construct a new RegexpConstraint.

        :Parameters:
         - `regexp`: (str) regular expression that strings must match
         - `flags`: (int) flags that are passed to re.compile()
        """
        super().__init__(msg)
        self.regexp: str = regexp
        self.flags: int = flags
        self._rgx = re.compile(regexp, flags)

    def __str__(self) -> str:
        return f"regexp {self.regexp}"

    def check_consistency(
        self,
        subjschema: yams_types.EntitySchema,
        objschema: yams_types.EntitySchema,
        rdef: yams_types.RelationDefinition,
    ) -> None:
        if not objschema.final:
            raise BadSchemaDefinition("regexp constraint doesn't apply to non " "final entity type")

        if objschema not in ("String", "Password"):
            raise BadSchemaDefinition(f"regexp constraint doesn't apply to {objschema} entity type")

    def check(self, entity, rtype: yams_types.RelationType, value: str) -> Optional[Match[str]]:
        """return true if the value maches the regular expression"""
        return self._rgx.match(value, self.flags)

    def _failed_message(self, entity, key: str, value) -> Tuple[str, Dict[str, Any]]:
        return (
            _("%(KEY-value)r doesn't match " "the %(KEY-regexp)r regular expression"),
            {key + "-value": value, key + "-regexp": self.regexp},
        )

    def serialize(self) -> str:
        """simple text serialization"""
        return cstr_json_dumps({"regexp": self.regexp, "flags": self.flags, "msg": self.msg})

    @classmethod
    def deserialize(cls, value: str) -> "RegexpConstraint":
        """simple text deserialization"""
        try:
            d = cstr_json_loads(value)
            return cls(**d)
        except ValueError:
            regexp, flags = value.rsplit(",", 1)
            return cls(regexp, int(flags))

    def __deepcopy__(self, memo) -> "RegexpConstraint":
        return RegexpConstraint(self.regexp, self.flags)


OPERATORS: Dict[str, Callable[[Any, Any], bool]] = {
    "<=": operator.le,
    "<": operator.lt,
    ">": operator.gt,
    ">=": operator.ge,
}

Comparable = Union[int, float, datetime.datetime, datetime.date, datetime.time]


class BoundaryConstraint(BaseConstraint):
    """the int/float bound constraint :

    set a minimal or maximal value to a numerical value
    """

    __implements__ = IConstraint

    def __init__(
        self,
        op: str,
        boundary: Optional[Union["Attribute", "NOW", "TODAY", Comparable]] = None,
        msg=None,
    ) -> None:
        super().__init__(msg)

        assert op in OPERATORS, op

        self.operator: str = op
        self.boundary: Optional[Union["Attribute", "NOW", "TODAY"]] = boundary

    def __str__(self) -> str:
        return f"value {self.serialize()}"

    def check_consistency(
        self,
        subjschema: yams_types.EntitySchema,
        objschema: yams_types.EntitySchema,
        rdef: yams_types.RelationDefinition,
    ) -> None:
        if isinstance(self.boundary, (NOW, TODAY)) and self.boundary.type != objschema.type:
            raise BadSchemaDefinition(
                f"boundary constraint {str(self.boundary)} applies to {self.boundary.type}"
                f" attributes, got {objschema.type}"
            )

        if not objschema.final:
            raise BadSchemaDefinition("boundary constraint doesn't apply to non final entity type")

    def check(self, entity, rtype: yams_types.RelationType, value) -> bool:
        """return true if the value satisfies the constraint, else false"""
        boundary = actual_value(self.boundary, entity)

        if boundary is None:
            return True

        return OPERATORS[self.operator](value, boundary)

    def _failed_message(self, entity, key: str, value) -> Tuple[str, Dict[str, Any]]:
        return (
            "value %%(KEY-value)s must be %s %%(KEY-boundary)s" % self.operator,
            {
                key + "-value": value,
                key + "-boundary": _message_value(self.boundary),
            },
        )

    def serialize(self) -> str:
        """simple text serialization"""
        return cstr_json_dumps({"op": self.operator, "boundary": self.boundary, "msg": self.msg})

    @classmethod
    def deserialize(cls: Type["BoundaryConstraint"], value: str) -> "BoundaryConstraint":
        """simple text deserialization"""
        try:
            d = cstr_json_loads(value)

            return cls(**d)
        except ValueError:
            op, boundary = value.split(" ", 1)

            return cls(op, eval(boundary))

    def type(self) -> str:
        return "BoundaryConstraint"


_("value %(KEY-value)s must be < %(KEY-boundary)s")
_("value %(KEY-value)s must be > %(KEY-boundary)s")
_("value %(KEY-value)s must be <= %(KEY-boundary)s")
_("value %(KEY-value)s must be >= %(KEY-boundary)s")


class IntervalBoundConstraint(BaseConstraint):
    """an int/float bound constraint :

    sets a minimal and / or a maximal value to a numerical value
    This class replaces the BoundConstraint class
    """

    __implements__ = IConstraint

    def __init__(
        self,
        *,
        minvalue: Optional[Comparable] = None,
        maxvalue: Optional[Comparable] = None,
        msg: Optional[str] = None,
    ) -> None:
        """
        :param minvalue: the minimal value that can be used
        :param maxvalue: the maxvalue value that can be used
        """
        assert not (minvalue is None and maxvalue is None)

        super().__init__(msg)

        self.minvalue: Optional[Comparable] = minvalue
        self.maxvalue: Optional[Comparable] = maxvalue

    def __str__(self) -> str:
        return f"value [{self.serialize()}]"

    def check_consistency(
        self,
        subjschema: yams_types.EntitySchema,
        objschema: yams_types.EntitySchema,
        rdef: yams_types.RelationDefinition,
    ) -> None:
        if not objschema.final:
            raise BadSchemaDefinition(
                "interval bound constraint doesn't apply" " to non final entity type"
            )

    def check(self, entity, rtype: yams_types.RelationType, value: Union[int, float]) -> bool:
        minvalue = actual_value(self.minvalue, entity)

        if minvalue is not None and value < minvalue:
            return False

        maxvalue = actual_value(self.maxvalue, entity)

        if maxvalue is not None and value > maxvalue:
            return False

        return True

    def _failed_message(self, entity, key: str, value) -> Tuple[str, Dict[str, Any]]:
        if self.minvalue is not None and value < actual_value(self.minvalue, entity):
            return (
                _("value %(KEY-value)s must be >= %(KEY-boundary)s"),
                {key + "-value": value, key + "-boundary": _message_value(self.minvalue)},
            )

        if self.maxvalue is not None and value > actual_value(self.maxvalue, entity):
            return (
                _("value %(KEY-value)s must be <= %(KEY-boundary)s"),
                {key + "-value": value, key + "-boundary": _message_value(self.maxvalue)},
            )

        assert False, "shouldnt be there"

    def serialize(self) -> str:
        """simple text serialization"""
        return cstr_json_dumps(
            {"minvalue": self.minvalue, "maxvalue": self.maxvalue, "msg": self.msg}
        )

    @classmethod
    def deserialize(cls: Type["IntervalBoundConstraint"], value: str) -> "IntervalBoundConstraint":
        """simple text deserialization"""
        try:
            d = cstr_json_loads(value)

            return cls(**d)
        except ValueError:
            minvalue, maxvalue = value.split(";")

            return cls(minvalue=eval(minvalue), maxvalue=eval(maxvalue))


class StaticVocabularyConstraint(BaseConstraint):
    """Enforces a predefined vocabulary set for the value."""

    __implements__ = IVocabularyConstraint

    def __init__(self, values: Sequence[str], msg: Optional[str] = None) -> None:
        super().__init__(msg)
        self.values: Tuple[str, ...] = tuple(values)

    def __str__(self) -> str:
        return f"value in ({', '.join(repr(str(word)) for word in self.vocabulary())})"

    def check(self, entity, rtype: yams_types.RelationType, value: str) -> bool:
        """return true if the value is in the specific vocabulary"""
        return value in self.vocabulary(entity=entity)

    def _failed_message(self, entity, key: str, value) -> Tuple[str, Dict[str, Any]]:
        if isinstance(value, str):
            value = f'"{str(value)}"'
            choices = ", ".join(f'"{val}"' for val in self.values)
        else:
            choices = ", ".join(str(val) for val in self.values)

        return (
            _("invalid value %(KEY-value)s, " "it must be one of %(KEY-choices)s"),
            {key + "-value": value, key + "-choices": choices},
        )

    def vocabulary(self, **kwargs) -> Tuple[str, ...]:
        """return a list of possible values for the attribute"""
        return self.values

    def serialize(self) -> str:
        """serialize possible values as a json object"""
        return cstr_json_dumps({"values": self.values, "msg": self.msg})

    @classmethod
    def deserialize(
        cls: Type["StaticVocabularyConstraint"], value: str
    ) -> "StaticVocabularyConstraint":
        """deserialize possible values from a csv list of evaluable strings"""
        try:
            values = cstr_json_loads(value)

            return cls(**values)
        except ValueError:
            interpreted_values = [eval(w) for w in re.split("(?<!,), ", value)]

            if interpreted_values and isinstance(interpreted_values[0], str):
                cast(List[str], interpreted_values)

                interpreted_values = [v.replace(",,", ",") for v in interpreted_values]

            return cls(interpreted_values)


class FormatConstraint(StaticVocabularyConstraint):
    regular_formats: Tuple[str, ...] = (
        _("text/rest"),
        _("text/markdown"),
        _("text/html"),
        _("text/plain"),
    )

    # **kwargs to have a common interface between all Constraint initializers
    def __init__(self, msg: Optional[str] = None, **kwargs) -> None:
        values: Tuple[str, ...] = self.regular_formats
        super().__init__(values, msg=msg)

    def check_consistency(
        self,
        subjschema: yams_types.EntitySchema,
        objschema: yams_types.EntitySchema,
        rdef: yams_types.RelationDefinition,
    ) -> None:
        if not objschema.final:
            raise BadSchemaDefinition("format constraint doesn't apply to non " "final entity type")

        if not objschema == "String":
            raise BadSchemaDefinition("format constraint only apply to String")


FORMAT_CONSTRAINT: FormatConstraint = FormatConstraint()


class MultipleStaticVocabularyConstraint(StaticVocabularyConstraint):
    """Enforce a list of values to be in a predefined set vocabulary."""

    # XXX never used

    def check(self, entity, rtype: yams_types.RelationType, values: Sequence[str]) -> bool:
        """return true if the values satisfy the constraint, else false"""
        vocab = self.vocabulary(entity=entity)

        for value in values:
            if value not in vocab:
                return False

        return True


# special classes to be used w/ constraints accepting values as argument(s):
# IntervalBoundConstraint


def actual_value(value, entity) -> Any:
    if hasattr(value, "value"):
        return value.value(entity)

    return value


class Attribute:
    def __init__(self, attr) -> None:
        self.attr = attr

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.attr!r})"

    def value(self, entity) -> Any:
        return getattr(entity, self.attr)


class NOW:
    def __init__(
        self,
        offset: Optional[datetime.timedelta] = None,
        type: Literal["Datetime", "TZDatetime"] = "TZDatetime",
    ) -> None:
        self.offset = offset
        # XXX no check that self.type is in KEYWORD_MAP?
        self.type = type

    def __str__(self):
        return f"{type(self).__name__}({self.offset}, {self.type})"

    def value(self, entity) -> datetime.datetime:
        now = yams.KEYWORD_MAP[self.type]["NOW"]()

        if self.offset:
            now += self.offset

        return cast(datetime.datetime, now)


class TODAY:
    def __init__(
        self,
        offset: Optional[datetime.timedelta] = None,
        type: Literal["Date", "Datetime", "TZDatetime"] = "Date",
    ) -> None:
        self.offset: Optional[datetime.timedelta] = offset
        # XXX no check that self.type is in KEYWORD_MAP?
        self.type: str = type

    def __str__(self):
        return f"{type(self).__name__}({self.offset}, {self.type})"

    def value(self, entity) -> datetime.date:
        now = yams.KEYWORD_MAP[self.type]["TODAY"]()

        if self.offset:
            now += self.offset

        return now


# base types checking functions ###############################################


def _check_no_error_during_convert(value: Any, convert_method) -> bool:
    try:
        convert_method(value)
    except ValueError:
        return False

    return True


def check_string(eschema, value) -> bool:
    """check value is an unicode string"""
    return isinstance(value, str)


def check_password(eschema, value) -> bool:
    """check value is an encoded string"""
    return isinstance(value, bytes)


def check_int(eschema, value) -> bool:
    """check value is an integer"""
    return _check_no_error_during_convert(value, int)


def check_float(eschema, value) -> bool:
    """check value is a float"""
    return _check_no_error_during_convert(value, float)


def check_decimal(eschema, value) -> bool:
    """check value is a Decimal"""
    try:
        decimal.Decimal(value)
    except (TypeError, decimal.InvalidOperation):
        return False

    return True


def check_boolean(eschema, value) -> bool:
    """check value is a boolean"""
    return isinstance(value, int)


def check_file(eschema, value) -> bool:
    """check value has a getvalue() method (e.g. StringIO or cStringIO)"""
    return hasattr(value, "getvalue")


def yes(*args, **kwargs) -> bool:
    """dunno how to check"""
    return True


# types converters #############################################################
def _str_to_datetime(value: str) -> datetime.datetime:
    try:
        return parse(value)
    except ValueError:
        try:
            return datetime.datetime.strptime(value, "%Y/%m/%d %H:%M")
        except ValueError:
            return datetime.datetime.strptime(value, "%Y/%m/%d")


def convert_datetime(value: Union[str, datetime.date, datetime.datetime]) -> datetime.datetime:
    # Note: use is __class__ since issubclass(datetime, date)
    if isinstance(value, str):
        if value in KEYWORD_MAP["Datetime"]:
            value = KEYWORD_MAP["Datetime"][value]()
        else:
            value = _str_to_datetime(value)
    elif type(value) is datetime.date:
        value = todatetime(value)

    if type(value) is not datetime.datetime:
        raise ValueError(f"Impossible to convert {value} to datetime")
    return value


def convert_date(value: Union[str, datetime.date, datetime.datetime]) -> datetime.date:
    if isinstance(value, str):
        if value in KEYWORD_MAP["Date"]:
            value = KEYWORD_MAP["Date"][value]()
        else:
            value = _str_to_datetime(value)
    if isinstance(value, datetime.datetime):
        value = todate(value)
    if type(value) is not datetime.date:
        raise ValueError(f"Impossible to convert {value} to date")
    return value


def convert_tzdatetime(value: Union[str, datetime.datetime, datetime.date]) -> datetime.datetime:
    if isinstance(value, str):
        if value in KEYWORD_MAP["TZDatetime"]:
            value = KEYWORD_MAP["TZDatetime"][value]()
        else:
            value = _str_to_datetime(value)
    # Note: use is __class__ since issubclass(datetime, date)
    if type(value) is datetime.date:
        value = todatetime(value)
    if type(value) is not datetime.datetime:
        raise ValueError(f"Impossible to convert {value} to tzdatetime")
    elif not hasattr(value, "tzinfo") or value.tzinfo is None:
        raise ValueError(
            f"You can't pass a datetime without timezone where of a tzdatetime is expected: {value}"
        )
    return value


def check_date(eschema, value: Any) -> bool:
    """Check value is date"""
    return _check_no_error_during_convert(value, convert_date)


def check_datetime(eschema, value: Any) -> bool:
    """Check value is datetime"""
    return _check_no_error_during_convert(value, convert_datetime)


def check_tzdatetime(eschema, value: Any) -> bool:
    """Check value is tzdatetime"""
    return _check_no_error_during_convert(value, convert_tzdatetime)


BASE_CHECKERS: yams_types.Checkers = {
    "Date": check_date,
    "Time": yes,
    "Datetime": check_datetime,
    "TZTime": check_tzdatetime,
    "TZDatetime": check_tzdatetime,
    "Interval": yes,
    "String": check_string,
    "Int": check_int,
    "BigInt": check_int,
    "Float": check_float,
    "Decimal": check_decimal,
    "Boolean": check_boolean,
    "Password": check_password,
    "Bytes": check_file,
}

BASE_CONVERTERS: yams_types.Converters = {
    "String": str,
    "Password": bytes,
    "Int": int,
    "BigInt": int,
    "Float": float,
    "Boolean": bool,
    "Decimal": decimal.Decimal,
    "Datetime": convert_datetime,
    "Date": convert_date,
    "TZDatetime": convert_tzdatetime,
    "TZTime": convert_tzdatetime,
}


def patch_sqlite_decimal() -> None:
    """patch Decimal checker and converter to bypass SQLITE Bug
    (SUM of Decimal return float in SQLITE)"""

    def convert_decimal(value) -> decimal.Decimal:
        # XXX issue a warning
        if isinstance(value, float):
            value = str(value)

        return decimal.Decimal(value)

    def check_decimal(eschema, value) -> bool:
        """check value is a Decimal"""
        try:
            if isinstance(value, float):
                return True

            decimal.Decimal(value)
        except (TypeError, decimal.InvalidOperation):
            return False

        return True

    BASE_CONVERTERS["Decimal"] = convert_decimal
    BASE_CHECKERS["Decimal"] = check_decimal
