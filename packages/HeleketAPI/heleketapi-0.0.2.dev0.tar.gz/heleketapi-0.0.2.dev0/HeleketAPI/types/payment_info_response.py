from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class PaymentInfoResponse:
    state: int
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PaymentInfoResponse:
    state: int
    uuid: str
    order_id: str
    amount: float
    payment_amount: float
    payment_amount_usd: float
    payer_amount: float
    discount_percent: float
    discount: float
    payer_currency: str
    currency: str
    merchant_amount: float
    network: str
    address: str
    payment_status: str
    url: str
    expired_at: int
    status: str
    is_final: bool
    created_at: datetime
    updated_at: datetime
    commission: float
    payer_amount_exchange_rate: str | None = None
    comments: str | None = None
    from_: str | None = field(default=None, metadata={"alias": "from"})
    txid: str | None = None
    additional_data: str | None = None
    address_qr_code: str | None = None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> PaymentInfoResponse:
        from_ = data["result"].pop("from", None)
        return cls(state=data["state"], from_=from_, **data["result"])