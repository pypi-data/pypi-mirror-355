from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ModelData(_message.Message):
    __slots__ = ("name", "version", "package_definition", "agent_classes")
    class JavaPackages(_message.Message):
        __slots__ = ("agents", "data_items", "portables")
        AGENTS_FIELD_NUMBER: _ClassVar[int]
        DATA_ITEMS_FIELD_NUMBER: _ClassVar[int]
        PORTABLES_FIELD_NUMBER: _ClassVar[int]
        agents: _containers.RepeatedScalarFieldContainer[str]
        data_items: _containers.RepeatedScalarFieldContainer[str]
        portables: _containers.RepeatedScalarFieldContainer[str]
        def __init__(self, agents: _Optional[_Iterable[str]] = ..., data_items: _Optional[_Iterable[str]] = ..., portables: _Optional[_Iterable[str]] = ...) -> None: ...
    class AgentClass(_message.Message):
        __slots__ = ("name_alias", "import_identifier", "language")
        class ImplementationLanguage(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            Java: _ClassVar[ModelData.AgentClass.ImplementationLanguage]
            Python: _ClassVar[ModelData.AgentClass.ImplementationLanguage]
        Java: ModelData.AgentClass.ImplementationLanguage
        Python: ModelData.AgentClass.ImplementationLanguage
        NAME_ALIAS_FIELD_NUMBER: _ClassVar[int]
        IMPORT_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
        LANGUAGE_FIELD_NUMBER: _ClassVar[int]
        name_alias: str
        import_identifier: str
        language: ModelData.AgentClass.ImplementationLanguage
        def __init__(self, name_alias: _Optional[str] = ..., import_identifier: _Optional[str] = ..., language: _Optional[_Union[ModelData.AgentClass.ImplementationLanguage, str]] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    PACKAGE_DEFINITION_FIELD_NUMBER: _ClassVar[int]
    AGENT_CLASSES_FIELD_NUMBER: _ClassVar[int]
    name: str
    version: str
    package_definition: ModelData.JavaPackages
    agent_classes: _containers.RepeatedCompositeFieldContainer[ModelData.AgentClass]
    def __init__(self, name: _Optional[str] = ..., version: _Optional[str] = ..., package_definition: _Optional[_Union[ModelData.JavaPackages, _Mapping]] = ..., agent_classes: _Optional[_Iterable[_Union[ModelData.AgentClass, _Mapping]]] = ...) -> None: ...
