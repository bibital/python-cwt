from typing import Any, Dict, List

from cryptography.hazmat.primitives.keywrap import aes_key_unwrap, aes_key_wrap

from ..const import COSE_KEY_OPERATION_VALUES
from ..exceptions import DecodeError, EncodeError
from ..recipient import Recipient


class AESKeyWrap(Recipient):
    _ACCEPTABLE_KEY_OPS = [
        COSE_KEY_OPERATION_VALUES["wrapKey"],
        COSE_KEY_OPERATION_VALUES["unwrapKey"],
    ]

    def __init__(
        self,
        protected: Dict[int, Any],
        unprotected: Dict[int, Any],
        ciphertext: bytes = b"",
        recipients: List[Any] = [],
        key_ops: List[int] = [],
        key: bytes = b"",
    ):
        super().__init__(protected, unprotected, ciphertext, recipients, key_ops, key)

        if self._alg == -3:  # A128KW
            if self._key and len(self._key) != 16:
                raise ValueError(f"Invalid key length: {len(self._key)}.")
        elif self._alg == -4:  # A192KW
            if self._key and len(self._key) != 24:
                raise ValueError(f"Invalid key length: {len(self._key)}.")
        elif self._alg == -5:  # A256KW
            if self._key and len(self._key) != 32:
                raise ValueError(f"Invalid key length: {len(self._key)}.")
        else:
            raise ValueError(f"Unknown alg(3) for AES key wrap: {self._alg}.")

    def wrap_key(self, key_to_wrap: bytes):
        try:
            self._ciphertext = aes_key_wrap(self._key, key_to_wrap)
        except Exception as err:
            raise EncodeError("Failed to wrap key.") from err

    def unwrap_key(self) -> bytes:
        try:
            return aes_key_unwrap(self._key, self._ciphertext)
        except Exception as err:
            raise DecodeError("Failed to unwrap key.") from err