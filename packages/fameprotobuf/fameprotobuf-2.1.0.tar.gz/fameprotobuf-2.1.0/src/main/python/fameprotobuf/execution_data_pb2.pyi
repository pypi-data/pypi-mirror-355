from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExecutionData(_message.Message):
    __slots__ = ("version_data", "simulation", "configuration")
    class VersionData(_message.Message):
        __slots__ = ("fame_protobuf", "fame_io", "fame_core", "python", "jvm", "os")
        FAME_PROTOBUF_FIELD_NUMBER: _ClassVar[int]
        FAME_IO_FIELD_NUMBER: _ClassVar[int]
        FAME_CORE_FIELD_NUMBER: _ClassVar[int]
        PYTHON_FIELD_NUMBER: _ClassVar[int]
        JVM_FIELD_NUMBER: _ClassVar[int]
        OS_FIELD_NUMBER: _ClassVar[int]
        fame_protobuf: str
        fame_io: str
        fame_core: str
        python: str
        jvm: str
        os: str
        def __init__(self, fame_protobuf: _Optional[str] = ..., fame_io: _Optional[str] = ..., fame_core: _Optional[str] = ..., python: _Optional[str] = ..., jvm: _Optional[str] = ..., os: _Optional[str] = ...) -> None: ...
    class Simulation(_message.Message):
        __slots__ = ("start", "duration_in_ms", "tick_count")
        START_FIELD_NUMBER: _ClassVar[int]
        DURATION_IN_MS_FIELD_NUMBER: _ClassVar[int]
        TICK_COUNT_FIELD_NUMBER: _ClassVar[int]
        start: str
        duration_in_ms: int
        tick_count: int
        def __init__(self, start: _Optional[str] = ..., duration_in_ms: _Optional[int] = ..., tick_count: _Optional[int] = ...) -> None: ...
    class ProcessConfiguration(_message.Message):
        __slots__ = ("core_count", "output_process", "output_interval")
        CORE_COUNT_FIELD_NUMBER: _ClassVar[int]
        OUTPUT_PROCESS_FIELD_NUMBER: _ClassVar[int]
        OUTPUT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
        core_count: int
        output_process: int
        output_interval: int
        def __init__(self, core_count: _Optional[int] = ..., output_process: _Optional[int] = ..., output_interval: _Optional[int] = ...) -> None: ...
    VERSION_DATA_FIELD_NUMBER: _ClassVar[int]
    SIMULATION_FIELD_NUMBER: _ClassVar[int]
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    version_data: ExecutionData.VersionData
    simulation: ExecutionData.Simulation
    configuration: ExecutionData.ProcessConfiguration
    def __init__(self, version_data: _Optional[_Union[ExecutionData.VersionData, _Mapping]] = ..., simulation: _Optional[_Union[ExecutionData.Simulation, _Mapping]] = ..., configuration: _Optional[_Union[ExecutionData.ProcessConfiguration, _Mapping]] = ...) -> None: ...
