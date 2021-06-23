from typing import Any, Dict, List, Optional, Union

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.asymmetric.x448 import X448PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey

from .algs.ec2 import EC2Key
from .algs.okp import OKPKey
from .cose_key_interface import COSEKeyInterface


class RecipientInterface(COSEKeyInterface):
    """
    The interface class for a COSE Recipient.
    """

    def __init__(
        self,
        protected: Optional[Dict[int, Any]] = None,
        unprotected: Optional[Dict[int, Any]] = None,
        ciphertext: bytes = b"",
        recipients: List[Any] = [],
        key_ops: List[int] = [],
        key: bytes = b"",
    ):

        """
        Constructor.

        Args:
            protected (Optional[Dict[int, Any]]): Parameters that are to be cryptographically
                protected.
            unprotected (Optional[Dict[int, Any]]): Parameters that are not cryptographically
                protected.
            ciphertext: A ciphertext encoded as bytes.
            recipients: A list of recipient information structures.
            key_ops: A list of operations that the key is to be used for.
            key: A body of the key as bytes.
        """
        protected = {} if protected is None else protected
        unprotected = {} if unprotected is None else unprotected

        params: Dict[int, Any] = {1: 4}  # Support only Symmetric key.

        # kid
        if 4 in unprotected:
            if not isinstance(unprotected[4], bytes):
                raise ValueError("unprotected[4](kid) should be bytes.")
            params[2] = unprotected[4]

        # alg
        if 1 in protected:
            if not isinstance(protected[1], int):
                raise ValueError("protected[1](alg) should be int.")
            params[3] = protected[1]
        elif 1 in unprotected:
            if not isinstance(unprotected[1], int):
                raise ValueError("unprotected[1](alg) should be int.")
            params[3] = unprotected[1]
            if params[3] == -6:  # direct
                if len(protected) != 0:
                    raise ValueError("protected header should be empty.")
                if len(ciphertext) != 0:
                    raise ValueError("ciphertext should be zero-length bytes.")
                if len(recipients) != 0:
                    raise ValueError("recipients should be absent.")
        else:
            params[3] = 0

        # key_ops
        if key_ops:
            params[4] = key_ops

        # iv
        if 5 in unprotected:
            if not isinstance(unprotected[5], bytes):
                raise ValueError("unprotected[5](iv) should be bytes.")
            params[5] = unprotected[5]

        super().__init__(params)

        self._protected = protected
        self._unprotected = unprotected
        self._ciphertext = ciphertext
        self._key = key

        # Validate recipients
        self._recipients: List[RecipientInterface] = []
        if not recipients:
            return
        for recipient in recipients:
            if not isinstance(recipient, RecipientInterface):
                raise ValueError("Invalid child recipient.")
            self._recipients.append(recipient)
        return

    @property
    def protected(self) -> Dict[int, Any]:
        """
        The parameters that are to be cryptographically protected.
        """
        return self._protected

    @property
    def unprotected(self) -> Dict[int, Any]:
        """
        The parameters that are not cryptographically protected.
        """
        return self._unprotected

    @property
    def ciphertext(self) -> bytes:
        """
        The ciphertext encoded as bytes
        """
        return self._ciphertext

    @property
    def recipients(self) -> Union[List[Any], None]:
        """
        The list of recipient information structures.
        """
        return self._recipients

    def to_list(self) -> List[Any]:
        """
        Returns the recipient information as a COSE recipient structure.

        Returns:
            List[Any]: The recipient structure.
        """
        b_protected = self._dumps(self._protected) if self._protected else b""
        b_ciphertext = self._ciphertext if self._ciphertext else b""
        res: List[Any] = [b_protected, self._unprotected, b_ciphertext]
        if not self._recipients:
            return res

        children = []
        for recipient in self._recipients:
            children.append(recipient.to_list())
        res.append(children)
        return res

    def encode_key(
        self,
        key: Optional[COSEKeyInterface] = None,
        recipient_key: Optional[COSEKeyInterface] = None,
        alg: Optional[int] = None,
        context: Optional[Union[List[Any], Dict[str, Any]]] = None,
    ) -> COSEKeyInterface:
        """
        Generates a MAC/encryption key with the recipient-specific method
        (e.g., key wrapping, key agreement, or the combination of them) and
        sets up the related information (context information or ciphertext)
        in the recipient structure. Therefore, it will be used by the sender
        of the recipient information before calling COSE.encode_* functions
        with the Recipient object. The key generated through this function
        will be set to ``key`` parameter of COSE.encode_* functions.

        Args:
            key (Optional[COSEKeyInterface]): The external key to
                be used for encoding the key.
            recipient_key (Optional[COSEKeyInterface]): The external public
                key provided by the recipient used for ECDH key agreement.
            alg (Optional[int]): The algorithm of the key generated.
            context (Optional[Union[List[Any], Dict[str, Any]]]): Context
                information structure.
        Returns:
            COSEKeyInterface: An encoded key which is used as ``key``
                parameter of COSE.encode_* functions.
        Raises:
            ValueError: Invalid arguments.
            EncodeError: Failed to encode(e.g., wrap, derive) the key.
        """
        raise NotImplementedError

    def decode_key(
        self,
        key: COSEKeyInterface,
        alg: Optional[int] = None,
        context: Optional[Union[List[Any], Dict[str, Any]]] = None,
    ) -> COSEKeyInterface:
        """
        Extracts a MAC/encryption key with the recipient-specific method
        (e.g., key wrapping, key agreement, or the combination of them).
        This function will be called in COSE.decode so applications do
        not need to call it directly.

        Args:
            key (COSEKeyInterface): The external key to be used for
                extracting the key.
            alg (Optional[int]): The algorithm of the key extracted.
            context (Optional[Union[List[Any], Dict[str, Any]]]): Context
                information structure.
        Returns:
            COSEKeyInterface: An extracted key which is used for decrypting
                or verifying a payload message.
        Raises:
            ValueError: Invalid arguments.
            DecodeError: Failed to decode(e.g., unwrap, derive) the key.
        """
        raise NotImplementedError

    def _to_cose_key(
        self, k: Union[EllipticCurvePublicKey, X25519PublicKey, X448PublicKey]
    ) -> Dict[int, Any]:
        if isinstance(k, EllipticCurvePublicKey):
            return EC2Key.to_cose_key(k)
        return OKPKey.to_cose_key(k)
