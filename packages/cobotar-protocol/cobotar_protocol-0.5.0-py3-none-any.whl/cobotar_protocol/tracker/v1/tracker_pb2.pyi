from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TrackerType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TRACKER_TYPE_UNSPECIFIED: _ClassVar[TrackerType]
    TRACKER_TYPE_QR_CODE: _ClassVar[TrackerType]
TRACKER_TYPE_UNSPECIFIED: TrackerType
TRACKER_TYPE_QR_CODE: TrackerType

class Tracker(_message.Message):
    __slots__ = ("id", "name", "reference", "frame", "type", "marker_text")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_FIELD_NUMBER: _ClassVar[int]
    FRAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    MARKER_TEXT_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    reference: str
    frame: str
    type: TrackerType
    marker_text: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., reference: _Optional[str] = ..., frame: _Optional[str] = ..., type: _Optional[_Union[TrackerType, str]] = ..., marker_text: _Optional[str] = ...) -> None: ...
