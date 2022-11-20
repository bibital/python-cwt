from typing import Any, Dict, List, Optional, Union

from ..const import COSE_KEY_OPERATION_VALUES
from ..cose_key import COSEKey
from ..cose_key_interface import COSEKeyInterface
from ..exceptions import DecodeError
from ..recipient_interface import RecipientInterface


class AESKeyWrap(RecipientInterface):
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
        sender_key: Optional[COSEKeyInterface] = None,
    ):
        if sender_key is None:
            raise ValueError("sender_key should be set.")
        if sender_key.alg not in [-3, -4, -5]:
            raise ValueError(f"Invalid alg in sender_key: {sender_key.alg}.")
        if 1 in protected and protected[1] != sender_key.alg:
            raise ValueError("algs in protected and sender_key do not match.")
        super().__init__(
            protected,
            unprotected,
            ciphertext,
            recipients,
            sender_key.key_ops,
            sender_key.key,
        )
        self._sender_key: COSEKeyInterface = sender_key

    def encode(
        self,
        plaintext: bytes = b"",
        salt: Optional[bytes] = None,
        external_aad: bytes = b"",
        aad_context: str = "Enc_Recipient",
    ) -> Optional[COSEKeyInterface]:

        self._ciphertext = self._sender_key.wrap_key(plaintext)
        return None

    def apply(
        self,
        key: Optional[COSEKeyInterface] = None,
        recipient_key: Optional[COSEKeyInterface] = None,
        salt: Optional[bytes] = None,
        context: Optional[Union[List[Any], Dict[str, Any]]] = None,
        external_aad: bytes = b"",
        aad_context: str = "Enc_Recipient",
    ) -> COSEKeyInterface:
        if not key:
            raise ValueError("key should be set.")
        if key.kid:
            self._protected[4] = key.kid
        self._ciphertext = self._sender_key.wrap_key(key.key)
        return key

    def extract(
        self,
        key: COSEKeyInterface,
        alg: Optional[int] = None,
        context: Optional[Union[List[Any], Dict[str, Any]]] = None,
    ) -> COSEKeyInterface:
        if not alg:
            raise ValueError("alg should be set.")
        try:
            unwrapped = key.unwrap_key(self._ciphertext)
            return COSEKey.from_symmetric_key(unwrapped, alg=alg, kid=self._kid)
        except Exception as err:
            raise DecodeError("Failed to decode key.") from err

    def decrypt(
        self,
        key: COSEKeyInterface,
        alg: Optional[int] = None,
        context: Optional[Union[List[Any], Dict[str, Any]]] = None,
        payload: bytes = b"",
        nonce: bytes = b"",
        aad: bytes = b"",
        external_aad: bytes = b"",
        aad_context: str = "Enc_Recipient",
    ) -> bytes:
        return self.extract(key, alg, context).decrypt(payload, nonce, aad)
