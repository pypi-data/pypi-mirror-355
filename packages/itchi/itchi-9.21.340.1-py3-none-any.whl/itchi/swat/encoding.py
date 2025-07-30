import math
from pydantic import BaseModel, ConfigDict

OBJECT_ENCODING_TIMESTAMP_SIZE = 16
OBJECT_ENCODING_TIMESTAMP_OFFSET = 16

OBJECT_ENCODING_STATUS_TYPE_NAME = "Status"
OBJECT_ENCODING_RUNNABLES_TYPE_NAME = "Runnables"
OBJECT_ENCODING_THREADS_TYPE_NAME = "Threads"


def size_to_mask(size: int, offset: int = 0) -> str:
    """Creates a mask for `size` bits at `offset`. Returns mask as a hex-string."""
    mask = (1 << size) - 1
    mask_with_offset = mask << offset
    return hex(mask_with_offset)


def bits_required(count: int) -> int:
    """Returns the number of bits required to represent `count` objects."""
    return math.ceil(math.log(count, 2))


class ObjectEncoding(BaseModel):
    """An object to represent an encoding for a specific SWAT object. Use cases:

    1. Calculate if a valid encoding exists.
    2. Render C defines for a specific encoding.
    3. Transform into winIDEA Profiler XML object.
    """

    model_config = ConfigDict(extra="forbid")

    core_id_offset: int = 0
    core_id_size: int = 0
    state_id_offset: int = 0
    state_id_size: int = 0
    object_id_offset: int = 0
    object_id_size: int = 0
    type_id_offset: int = 0
    type_id_size: int = 0
    type_id_key: int = 0
    type_id_name: str = ""
    timestamp_offset: int = 0
    timestamp_size: int = 0

    def __init__(self, num_cores: int, num_types: int):
        """Initialize an ObjectEncoding with the number of cores and types."""
        super().__init__()
        core_id_size = bits_required(num_cores)
        type_id_size = bits_required(num_types)

        self.timestamp_offset = OBJECT_ENCODING_TIMESTAMP_OFFSET
        self.timestamp_size = OBJECT_ENCODING_TIMESTAMP_SIZE
        self.type_id_offset = 0
        self.type_id_size = type_id_size
        self.core_id_offset = type_id_size  # core_id is right next to type_id
        self.core_id_size = core_id_size

    def get_payload_offset(self):
        """Get the offset from which on state and object can be encoded."""
        assert self.type_id_offset == 0
        return self.type_id_size + self.core_id_size

    def get_max_payload_size(self):
        """Get maximum number of bits that can be used to encode state and object."""
        return 32 - self.timestamp_size - self.type_id_size - self.core_id_size

    def into_status(self, type_id_key: int):
        """Update this object to represent status encoding."""
        self.type_id_key = type_id_key
        self.type_id_name = OBJECT_ENCODING_STATUS_TYPE_NAME
        return self

    def into_signal_u32(self, type_id_key: int, signal_name: str):
        """Update this object to encode a u32 signal."""
        self.type_id_key = type_id_key
        self.type_id_name = signal_name
        self.state_id_offset = 32
        self.state_id_size = 32
        return self

    def into_signal_u8(self, type_id_key: int, signal_name: str):
        """Update this object to encode a u32 signal."""
        self.type_id_key = type_id_key
        self.type_id_name = signal_name
        self.state_id_offset = self.get_payload_offset()
        if self.get_max_payload_size() < 8:
            raise ValueError("Not enough bits available for u8 signal encoding")
        self.state_id_size = 8
        return self
