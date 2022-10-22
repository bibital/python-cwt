from typing import Any, Dict, List, Optional, Union

from ..cose_key_interface import COSEKeyInterface, HPKECipherSuite
from ..recipient_interface import RecipientInterface


class HPKE(RecipientInterface):
    def __init__(
        self,
        protected: Dict[int, Any],
        unprotected: Dict[int, Any],
        ciphertext: bytes = b"",
        recipients: List[Any] = [],
    ):
        super().__init__(protected, unprotected, ciphertext, recipients)

        if self._alg != -1:
            raise ValueError("alg should be HPKE(-1).")
        if -4 not in unprotected:
            raise ValueError("HPKE sender information(-4) not found.")
        if 1 not in unprotected[-4]:
            raise ValueError("kem id(1) not found in HPKE sender information(-4).")
        if 5 not in unprotected[-4]:
            raise ValueError("kdf id(5) not found in HPKE sender information(-4).")
        if 2 not in unprotected[-4]:
            raise ValueError("aead id(2) not found in HPKE sender information(-4).")
        self._suite = HPKECipherSuite(unprotected[-4][1], unprotected[-4][5], unprotected[-4][2])
        return

    def apply(
        self,
        key: Optional[COSEKeyInterface] = None,
        recipient_key: Optional[COSEKeyInterface] = None,
        salt: Optional[bytes] = None,
        context: Optional[Union[List[Any], Dict[str, Any]]] = None,
    ) -> COSEKeyInterface:
        if not recipient_key:
            raise ValueError("recipient_key should be set.")

        self._recipient_key = recipient_key
        return self._recipient_key

    def to_list(self, payload: bytes = b"", aad: bytes = b"") -> List[Any]:
        enc, self._ciphertext = self._recipient_key.seal(self._suite, payload, aad)
        self._unprotected[-4][3] = enc
        return super().to_list(payload, aad)

    def open(
        self,
        key: COSEKeyInterface,
        aad: bytes,
    ) -> bytes:
        return key.open(self._suite, self._unprotected[-4][3], self._ciphertext, aad)
