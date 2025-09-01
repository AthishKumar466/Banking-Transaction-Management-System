from dataclasses import dataclass
from typing import Optional

@dataclass
class Account:
    id: Optional[int]
    name: str
    balance: float
    created_at: Optional[str] = None

@dataclass
class Transaction:
    id: Optional[int]
    account_id: int
    type: str
    amount: float
    counterparty: Optional[int]
    note: Optional[str]
    created_at: Optional[str] = None
