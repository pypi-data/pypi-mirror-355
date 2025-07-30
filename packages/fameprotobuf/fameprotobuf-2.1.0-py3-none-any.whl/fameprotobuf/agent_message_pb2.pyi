from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProtoDataItem(_message.Message):
    __slots__ = ("data_type_id", "bool_values", "int_values", "long_values", "float_values", "double_values", "string_values")
    DATA_TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUES_FIELD_NUMBER: _ClassVar[int]
    INT_VALUES_FIELD_NUMBER: _ClassVar[int]
    LONG_VALUES_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUES_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUES_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUES_FIELD_NUMBER: _ClassVar[int]
    data_type_id: int
    bool_values: _containers.RepeatedScalarFieldContainer[bool]
    int_values: _containers.RepeatedScalarFieldContainer[int]
    long_values: _containers.RepeatedScalarFieldContainer[int]
    float_values: _containers.RepeatedScalarFieldContainer[float]
    double_values: _containers.RepeatedScalarFieldContainer[float]
    string_values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, data_type_id: _Optional[int] = ..., bool_values: _Optional[_Iterable[bool]] = ..., int_values: _Optional[_Iterable[int]] = ..., long_values: _Optional[_Iterable[int]] = ..., float_values: _Optional[_Iterable[float]] = ..., double_values: _Optional[_Iterable[float]] = ..., string_values: _Optional[_Iterable[str]] = ...) -> None: ...

class NestedItem(_message.Message):
    __slots__ = ("data_type_id", "bool_values", "int_values", "long_values", "float_values", "double_values", "string_values", "time_series_ids", "components")
    DATA_TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUES_FIELD_NUMBER: _ClassVar[int]
    INT_VALUES_FIELD_NUMBER: _ClassVar[int]
    LONG_VALUES_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUES_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUES_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUES_FIELD_NUMBER: _ClassVar[int]
    TIME_SERIES_IDS_FIELD_NUMBER: _ClassVar[int]
    COMPONENTS_FIELD_NUMBER: _ClassVar[int]
    data_type_id: int
    bool_values: _containers.RepeatedScalarFieldContainer[bool]
    int_values: _containers.RepeatedScalarFieldContainer[int]
    long_values: _containers.RepeatedScalarFieldContainer[int]
    float_values: _containers.RepeatedScalarFieldContainer[float]
    double_values: _containers.RepeatedScalarFieldContainer[float]
    string_values: _containers.RepeatedScalarFieldContainer[str]
    time_series_ids: _containers.RepeatedScalarFieldContainer[int]
    components: _containers.RepeatedCompositeFieldContainer[NestedItem]
    def __init__(self, data_type_id: _Optional[int] = ..., bool_values: _Optional[_Iterable[bool]] = ..., int_values: _Optional[_Iterable[int]] = ..., long_values: _Optional[_Iterable[int]] = ..., float_values: _Optional[_Iterable[float]] = ..., double_values: _Optional[_Iterable[float]] = ..., string_values: _Optional[_Iterable[str]] = ..., time_series_ids: _Optional[_Iterable[int]] = ..., components: _Optional[_Iterable[_Union[NestedItem, _Mapping]]] = ...) -> None: ...

class ProtoMessage(_message.Message):
    __slots__ = ("sender_id", "receiver_id", "data_items", "nested_items")
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_ID_FIELD_NUMBER: _ClassVar[int]
    DATA_ITEMS_FIELD_NUMBER: _ClassVar[int]
    NESTED_ITEMS_FIELD_NUMBER: _ClassVar[int]
    sender_id: int
    receiver_id: int
    data_items: _containers.RepeatedCompositeFieldContainer[ProtoDataItem]
    nested_items: _containers.RepeatedCompositeFieldContainer[NestedItem]
    def __init__(self, sender_id: _Optional[int] = ..., receiver_id: _Optional[int] = ..., data_items: _Optional[_Iterable[_Union[ProtoDataItem, _Mapping]]] = ..., nested_items: _Optional[_Iterable[_Union[NestedItem, _Mapping]]] = ...) -> None: ...
