from typing import Optional, Dict, Union, Any
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class SequencedReceiptContent(BaseModel):
    """Content of a successful sequenced receipt."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    nonce: str
    request_hash: str
    request_index: int
    sender: str
    enclave_signature: str


class ErrorReceiptContent(BaseModel):
    """Content of an error receipt."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    message: str


class TradeReceipt(BaseModel):
    """Model for trade request receipts."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    t: str  # "Sequenced" or "Error"
    c: Union[SequencedReceiptContent, ErrorReceiptContent, Dict[str, Any]]

    @property
    def is_success(self) -> bool:
        """Check if the receipt indicates success."""

        return self.t == "Sequenced"

    @property
    def is_error(self) -> bool:
        """Check if the receipt indicates an error."""

        return self.t == "Error"

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message if this is an error receipt."""

        if self.is_error and isinstance(self.c, ErrorReceiptContent):
            return self.c.message
        return None
