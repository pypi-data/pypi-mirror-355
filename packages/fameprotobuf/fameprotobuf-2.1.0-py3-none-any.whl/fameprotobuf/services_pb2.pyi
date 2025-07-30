from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ScheduledTime(_message.Message):
    __slots__ = ("time_step",)
    TIME_STEP_FIELD_NUMBER: _ClassVar[int]
    time_step: int
    def __init__(self, time_step: _Optional[int] = ...) -> None: ...

class WarmUpMessage(_message.Message):
    __slots__ = ("needed",)
    NEEDED_FIELD_NUMBER: _ClassVar[int]
    needed: bool
    def __init__(self, needed: bool = ...) -> None: ...

class Output(_message.Message):
    __slots__ = ("agent_types", "series")
    class AgentType(_message.Message):
        __slots__ = ("class_name", "fields")
        class Field(_message.Message):
            __slots__ = ("field_id", "field_name", "index_names")
            FIELD_ID_FIELD_NUMBER: _ClassVar[int]
            FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
            INDEX_NAMES_FIELD_NUMBER: _ClassVar[int]
            field_id: int
            field_name: str
            index_names: _containers.RepeatedScalarFieldContainer[str]
            def __init__(self, field_id: _Optional[int] = ..., field_name: _Optional[str] = ..., index_names: _Optional[_Iterable[str]] = ...) -> None: ...
        CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
        FIELDS_FIELD_NUMBER: _ClassVar[int]
        class_name: str
        fields: _containers.RepeatedCompositeFieldContainer[Output.AgentType.Field]
        def __init__(self, class_name: _Optional[str] = ..., fields: _Optional[_Iterable[_Union[Output.AgentType.Field, _Mapping]]] = ...) -> None: ...
    class Series(_message.Message):
        __slots__ = ("class_name", "agent_id", "lines")
        class Line(_message.Message):
            __slots__ = ("time_step", "columns")
            class Column(_message.Message):
                __slots__ = ("field_id", "value", "entries")
                class Map(_message.Message):
                    __slots__ = ("index_values", "value")
                    INDEX_VALUES_FIELD_NUMBER: _ClassVar[int]
                    VALUE_FIELD_NUMBER: _ClassVar[int]
                    index_values: _containers.RepeatedScalarFieldContainer[str]
                    value: str
                    def __init__(self, index_values: _Optional[_Iterable[str]] = ..., value: _Optional[str] = ...) -> None: ...
                FIELD_ID_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                ENTRIES_FIELD_NUMBER: _ClassVar[int]
                field_id: int
                value: float
                entries: _containers.RepeatedCompositeFieldContainer[Output.Series.Line.Column.Map]
                def __init__(self, field_id: _Optional[int] = ..., value: _Optional[float] = ..., entries: _Optional[_Iterable[_Union[Output.Series.Line.Column.Map, _Mapping]]] = ...) -> None: ...
            TIME_STEP_FIELD_NUMBER: _ClassVar[int]
            COLUMNS_FIELD_NUMBER: _ClassVar[int]
            time_step: int
            columns: _containers.RepeatedCompositeFieldContainer[Output.Series.Line.Column]
            def __init__(self, time_step: _Optional[int] = ..., columns: _Optional[_Iterable[_Union[Output.Series.Line.Column, _Mapping]]] = ...) -> None: ...
        CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
        AGENT_ID_FIELD_NUMBER: _ClassVar[int]
        LINES_FIELD_NUMBER: _ClassVar[int]
        class_name: str
        agent_id: int
        lines: _containers.RepeatedCompositeFieldContainer[Output.Series.Line]
        def __init__(self, class_name: _Optional[str] = ..., agent_id: _Optional[int] = ..., lines: _Optional[_Iterable[_Union[Output.Series.Line, _Mapping]]] = ...) -> None: ...
    AGENT_TYPES_FIELD_NUMBER: _ClassVar[int]
    SERIES_FIELD_NUMBER: _ClassVar[int]
    agent_types: _containers.RepeatedCompositeFieldContainer[Output.AgentType]
    series: _containers.RepeatedCompositeFieldContainer[Output.Series]
    def __init__(self, agent_types: _Optional[_Iterable[_Union[Output.AgentType, _Mapping]]] = ..., series: _Optional[_Iterable[_Union[Output.Series, _Mapping]]] = ...) -> None: ...

class AddressBook(_message.Message):
    __slots__ = ("process_id", "agent_ids")
    PROCESS_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_IDS_FIELD_NUMBER: _ClassVar[int]
    process_id: int
    agent_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, process_id: _Optional[int] = ..., agent_ids: _Optional[_Iterable[int]] = ...) -> None: ...
