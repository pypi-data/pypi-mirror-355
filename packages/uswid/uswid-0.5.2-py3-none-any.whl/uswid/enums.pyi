from enum import IntEnum

class uSwidVersionScheme(IntEnum):
    UNKNOWN = 0
    MULTIPARTNUMERIC = 1
    MULTIPARTNUMERIC_SUFFIX = 2
    ALPHANUMERIC = 3
    DECIMAL = 4
    SEMVER = 16384
    @classmethod
    def from_version(cls, version: str) -> uSwidVersionScheme: ...

USWID_HEADER_MAGIC: bytes
USWID_HEADER_FLAG_COMPRESSED: int

class uSwidHeaderFlags(IntEnum):
    NONE = 0
    COMPRESSED = 1

class uSwidPayloadCompression(IntEnum):
    NONE = 0
    ZLIB = 1
    LZMA = 2
    @staticmethod
    def argparse(s): ...
