from fameprotobuf import agent_message_pb2 as _agent_message_pb2
from fameprotobuf import services_pb2 as _services_pb2
from fameprotobuf import input_file_pb2 as _input_file_pb2
from fameprotobuf import model_pb2 as _model_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MpiMessage(_message.Message):
    __slots__ = ("scheduled_time", "warm_up", "address_book", "input", "output", "messages", "model")
    SCHEDULED_TIME_FIELD_NUMBER: _ClassVar[int]
    WARM_UP_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_BOOK_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    scheduled_time: _services_pb2.ScheduledTime
    warm_up: _services_pb2.WarmUpMessage
    address_book: _services_pb2.AddressBook
    input: _input_file_pb2.InputData
    output: _services_pb2.Output
    messages: _containers.RepeatedCompositeFieldContainer[_agent_message_pb2.ProtoMessage]
    model: _model_pb2.ModelData
    def __init__(self, scheduled_time: _Optional[_Union[_services_pb2.ScheduledTime, _Mapping]] = ..., warm_up: _Optional[_Union[_services_pb2.WarmUpMessage, _Mapping]] = ..., address_book: _Optional[_Union[_services_pb2.AddressBook, _Mapping]] = ..., input: _Optional[_Union[_input_file_pb2.InputData, _Mapping]] = ..., output: _Optional[_Union[_services_pb2.Output, _Mapping]] = ..., messages: _Optional[_Iterable[_Union[_agent_message_pb2.ProtoMessage, _Mapping]]] = ..., model: _Optional[_Union[_model_pb2.ModelData, _Mapping]] = ...) -> None: ...

class Bundle(_message.Message):
    __slots__ = ("messages",)
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[MpiMessage]
    def __init__(self, messages: _Optional[_Iterable[_Union[MpiMessage, _Mapping]]] = ...) -> None: ...
