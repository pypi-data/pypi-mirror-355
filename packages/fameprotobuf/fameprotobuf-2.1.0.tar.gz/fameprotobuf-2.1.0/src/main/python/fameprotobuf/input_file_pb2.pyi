from fameprotobuf import contract_pb2 as _contract_pb2
from fameprotobuf import field_pb2 as _field_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class InputData(_message.Message):
    __slots__ = ("run_id", "simulation", "time_series", "agents", "contracts", "schema", "string_sets", "metadata")
    class SimulationParam(_message.Message):
        __slots__ = ("start_time", "stop_time", "random_seed")
        START_TIME_FIELD_NUMBER: _ClassVar[int]
        STOP_TIME_FIELD_NUMBER: _ClassVar[int]
        RANDOM_SEED_FIELD_NUMBER: _ClassVar[int]
        start_time: int
        stop_time: int
        random_seed: int
        def __init__(self, start_time: _Optional[int] = ..., stop_time: _Optional[int] = ..., random_seed: _Optional[int] = ...) -> None: ...
    class TimeSeriesDao(_message.Message):
        __slots__ = ("series_id", "series_name", "time_steps", "values")
        SERIES_ID_FIELD_NUMBER: _ClassVar[int]
        SERIES_NAME_FIELD_NUMBER: _ClassVar[int]
        TIME_STEPS_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        series_id: int
        series_name: str
        time_steps: _containers.RepeatedScalarFieldContainer[int]
        values: _containers.RepeatedScalarFieldContainer[float]
        def __init__(self, series_id: _Optional[int] = ..., series_name: _Optional[str] = ..., time_steps: _Optional[_Iterable[int]] = ..., values: _Optional[_Iterable[float]] = ...) -> None: ...
    class AgentDao(_message.Message):
        __slots__ = ("id", "class_name", "fields", "metadata")
        ID_FIELD_NUMBER: _ClassVar[int]
        CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
        FIELDS_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        id: int
        class_name: str
        fields: _containers.RepeatedCompositeFieldContainer[_field_pb2.NestedField]
        metadata: str
        def __init__(self, id: _Optional[int] = ..., class_name: _Optional[str] = ..., fields: _Optional[_Iterable[_Union[_field_pb2.NestedField, _Mapping]]] = ..., metadata: _Optional[str] = ...) -> None: ...
    class StringSetDao(_message.Message):
        __slots__ = ("name", "values", "metadata")
        class StringSetEntry(_message.Message):
            __slots__ = ("name", "metadata")
            NAME_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            name: str
            metadata: str
            def __init__(self, name: _Optional[str] = ..., metadata: _Optional[str] = ...) -> None: ...
        NAME_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        name: str
        values: _containers.RepeatedCompositeFieldContainer[InputData.StringSetDao.StringSetEntry]
        metadata: str
        def __init__(self, name: _Optional[str] = ..., values: _Optional[_Iterable[_Union[InputData.StringSetDao.StringSetEntry, _Mapping]]] = ..., metadata: _Optional[str] = ...) -> None: ...
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    SIMULATION_FIELD_NUMBER: _ClassVar[int]
    TIME_SERIES_FIELD_NUMBER: _ClassVar[int]
    AGENTS_FIELD_NUMBER: _ClassVar[int]
    CONTRACTS_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    STRING_SETS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    run_id: int
    simulation: InputData.SimulationParam
    time_series: _containers.RepeatedCompositeFieldContainer[InputData.TimeSeriesDao]
    agents: _containers.RepeatedCompositeFieldContainer[InputData.AgentDao]
    contracts: _containers.RepeatedCompositeFieldContainer[_contract_pb2.ProtoContract]
    schema: str
    string_sets: _containers.RepeatedCompositeFieldContainer[InputData.StringSetDao]
    metadata: str
    def __init__(self, run_id: _Optional[int] = ..., simulation: _Optional[_Union[InputData.SimulationParam, _Mapping]] = ..., time_series: _Optional[_Iterable[_Union[InputData.TimeSeriesDao, _Mapping]]] = ..., agents: _Optional[_Iterable[_Union[InputData.AgentDao, _Mapping]]] = ..., contracts: _Optional[_Iterable[_Union[_contract_pb2.ProtoContract, _Mapping]]] = ..., schema: _Optional[str] = ..., string_sets: _Optional[_Iterable[_Union[InputData.StringSetDao, _Mapping]]] = ..., metadata: _Optional[str] = ...) -> None: ...
