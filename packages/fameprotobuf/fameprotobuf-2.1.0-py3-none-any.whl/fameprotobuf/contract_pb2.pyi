from fameprotobuf import field_pb2 as _field_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProtoContract(_message.Message):
    __slots__ = ("sender_id", "receiver_id", "product_name", "first_delivery_time", "delivery_interval_in_steps", "expiration_time", "fields", "metadata")
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_ID_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_NAME_FIELD_NUMBER: _ClassVar[int]
    FIRST_DELIVERY_TIME_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_INTERVAL_IN_STEPS_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_TIME_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    sender_id: int
    receiver_id: int
    product_name: str
    first_delivery_time: int
    delivery_interval_in_steps: int
    expiration_time: int
    fields: _containers.RepeatedCompositeFieldContainer[_field_pb2.NestedField]
    metadata: str
    def __init__(self, sender_id: _Optional[int] = ..., receiver_id: _Optional[int] = ..., product_name: _Optional[str] = ..., first_delivery_time: _Optional[int] = ..., delivery_interval_in_steps: _Optional[int] = ..., expiration_time: _Optional[int] = ..., fields: _Optional[_Iterable[_Union[_field_pb2.NestedField, _Mapping]]] = ..., metadata: _Optional[str] = ...) -> None: ...
