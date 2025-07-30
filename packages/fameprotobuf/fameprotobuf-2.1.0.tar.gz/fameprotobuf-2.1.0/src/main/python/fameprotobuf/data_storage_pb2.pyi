from fameprotobuf import services_pb2 as _services_pb2
from fameprotobuf import input_file_pb2 as _input_file_pb2
from fameprotobuf import execution_data_pb2 as _execution_data_pb2
from fameprotobuf import model_pb2 as _model_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DataStorage(_message.Message):
    __slots__ = ("input", "output", "execution", "model")
    INPUT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    input: _input_file_pb2.InputData
    output: _services_pb2.Output
    execution: _execution_data_pb2.ExecutionData
    model: _model_pb2.ModelData
    def __init__(self, input: _Optional[_Union[_input_file_pb2.InputData, _Mapping]] = ..., output: _Optional[_Union[_services_pb2.Output, _Mapping]] = ..., execution: _Optional[_Union[_execution_data_pb2.ExecutionData, _Mapping]] = ..., model: _Optional[_Union[_model_pb2.ModelData, _Mapping]] = ...) -> None: ...
