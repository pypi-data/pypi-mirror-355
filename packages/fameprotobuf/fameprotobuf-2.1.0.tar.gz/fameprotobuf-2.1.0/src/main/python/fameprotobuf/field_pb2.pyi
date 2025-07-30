from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NestedField(_message.Message):
    __slots__ = ("field_name", "series_id", "int_values", "string_values", "double_values", "fields", "long_values", "is_list", "metadata")
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    SERIES_ID_FIELD_NUMBER: _ClassVar[int]
    INT_VALUES_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUES_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUES_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    LONG_VALUES_FIELD_NUMBER: _ClassVar[int]
    IS_LIST_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    field_name: str
    series_id: int
    int_values: _containers.RepeatedScalarFieldContainer[int]
    string_values: _containers.RepeatedScalarFieldContainer[str]
    double_values: _containers.RepeatedScalarFieldContainer[float]
    fields: _containers.RepeatedCompositeFieldContainer[NestedField]
    long_values: _containers.RepeatedScalarFieldContainer[int]
    is_list: bool
    metadata: str
    def __init__(self, field_name: _Optional[str] = ..., series_id: _Optional[int] = ..., int_values: _Optional[_Iterable[int]] = ..., string_values: _Optional[_Iterable[str]] = ..., double_values: _Optional[_Iterable[float]] = ..., fields: _Optional[_Iterable[_Union[NestedField, _Mapping]]] = ..., long_values: _Optional[_Iterable[int]] = ..., is_list: bool = ..., metadata: _Optional[str] = ...) -> None: ...
