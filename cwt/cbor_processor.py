from cbor2 import dumps, loads
from typing import Any, Dict

from .exceptions import DecodeError, EncodeError


class CBORProcessor:

    def _dumps(self, obj: Dict[int, Any]) -> bytes:
        try:
            return dumps(obj)
        except Exception as err:
            raise DecodeError("Failed to decode.") from err

    def _loads(self, s: bytes) -> Dict[int, Any]:
        try:
            return loads(s)
        except Exception as err:
            raise EncodeError("Failed to encode.") from err
