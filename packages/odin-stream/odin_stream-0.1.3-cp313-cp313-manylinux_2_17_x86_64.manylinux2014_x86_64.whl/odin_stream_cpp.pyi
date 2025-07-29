from typing import overload

import pyarrow.lib


class PrimitiveTypeDescriptor:
    def __init__(self, name: str, size: int, arrow_data_type: "arrow::DataType") -> None: ...

    def get_size(self) -> int:
        """Get the size of the primitive type descriptor"""

    def get_arrow_type(self) -> "arrow::DataType":
        """Get the Arrow data type"""

    def get_name(self) -> str:
        """Get the name of the primitive type descriptor"""

    @staticmethod
    def get_by_name(name: str) -> PrimitiveTypeDescriptor:
        """Get the primitive type descriptor by name"""

    def __repr__(self) -> str:
        """Get string representation of the primitive type descriptor"""

class CompositeTypeDescriptor:
    def __init__(self) -> None: ...

    @overload
    def add_member(self, name: str, descriptor: PrimitiveTypeDescriptor) -> None: ...

    @overload
    def add_member(self, name: str, descriptor: CompositeTypeDescriptor) -> None: ...

    def get_size(self) -> int:
        """Get the size of the composite type descriptor"""

    def __repr__(self) -> str:
        """Get string representation of the composite type descriptor"""

class ParameterDescriptor:
    @overload
    def __init__(self, id: int, name: str, type_descriptor: PrimitiveTypeDescriptor) -> None: ...

    @overload
    def __init__(self, id: int, name: str, type_descriptor: CompositeTypeDescriptor) -> None: ...

    def get_id(self) -> int:
        """Get the ID of the parameter"""

    def get_name(self) -> str:
        """Get the name of the parameter"""

    def get_type_descriptor(self) -> "GenericTypeDescriptor":
        """Get the type descriptor of the parameter"""

    def get_size(self) -> int:
        """Get the size of the parameter"""

    @staticmethod
    def unknown_type(id: int, name: str) -> ParameterDescriptor:
        """Create an unknown type parameter descriptor"""

    def __repr__(self) -> str:
        """Get string representation of the parameter descriptor"""

class ParameterMapDescriptor:
    @overload
    def __init__(self, parameter_map: dict) -> None:
        """
        Constructor for the ParameterMapDescriptor. Initializes with parameter map.
        """

    @overload
    def __init__(self) -> None: ...

    def find_by_id(self, key: int) -> "std::optional<std::shared_ptr<ParameterDescriptor> >":
        """Get a ParameterDescriptor by its key."""

    def find_by_name(self, name: str) -> "std::optional<std::shared_ptr<ParameterDescriptor> >":
        """Get a ParameterDescriptor by its name."""

    def add_parameter(self, parameter: ParameterDescriptor) -> None:
        """Add a parameter to the map."""

    def __repr__(self) -> str:
        """Get string representation of the parameter map descriptor."""

class FixedSizeParameter:
    def __init__(self, index: int, size: int, parameter: ParameterDescriptor) -> None:
        """
        Create a new FixedSizeParameter with the given index, size, and parmameter.
        """

    def get_index(self) -> int:
        """Get the index of the parameter."""

    def get_size(self) -> int:
        """Get the size of the parameter."""

    def get_parameter(self) -> ParameterDescriptor:
        """Get the parameter descriptor."""

    def __repr__(self) -> str: ...

class ParameterSet:
    """Manages a set of streaming parameters"""

    def __init__(self, identifier: int, definition_identifier: int, type_descriptors: ParameterMapDescriptor) -> None:
        """
        Create a new ParameterSet with the given identifier and type descriptors.
        """

    @staticmethod
    def from_identifier_data(data: bytes, type_descriptors: ParameterMapDescriptor) -> ParameterSet:
        """Create a new ParameterSet from identifier data."""

    def flush_to_arrow_table(self) -> pyarrow.lib.Table:
        """
        Creates an Arrow table from the data in the parameters and clears them.
        """

class StreamProcessor:
    def __init__(self, parameter_map: ParameterMapDescriptor, silent_errors: bool = False) -> None:
        """
        Constructor for the StreamProcessor. Initializes with the parameter map.
        """

    def process_packets(self, bytes_list: list) -> None:
        """Process a list of bytes."""

    def get_parameter_set(self, identifier: int) -> ParameterSet:
        """Get a ParameterSet by its identifier."""

    def clear_parameter_sets(self) -> None:
        """Clear all stored ParameterSets."""

    def get_parameter_set_identifiers(self) -> list[int]:
        """Get a list of all stored ParameterSet identifiers."""

    @property
    def statistics(self) -> OdinStreamStatistics:
        """Get the statistics of the stream processor."""

class OdinStreamStatistics:
    def __init__(self) -> None: ...

    @property
    def identifier_decoding_errors(self) -> int: ...

    @property
    def data_decoding_errors(self) -> int: ...

    @property
    def event_decoding_errors(self) -> int: ...

    @property
    def other_errors(self) -> int: ...

    @property
    def received_events_packets(self) -> int: ...

    @property
    def received_identifier_packets(self) -> int: ...

    @property
    def received_data_packets(self) -> int: ...

    @property
    def received_unresolved_data_packets(self) -> int: ...

    @property
    def received_other_packets(self) -> int: ...

    def __repr__(self) -> str: ...
