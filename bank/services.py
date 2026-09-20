from typing import List, Optional
from .db import get_conn
from .models import Account, Transaction


def _to_cents(amount: float) -> int:
    return round(amount * 100)


def _to_dollars(cents: int) -> float:
    return cents / 100


def _account_from_row(row) -> Account:
    return Account(id=row['id'], name=row['name'], balance=_to_dollars(row['balance']), created_at=row['created_at'])


def _transaction_from_row(row) -> Transaction:
    return Transaction(
        id=row['id'],
        account_id=row['account_id'],
        type=row['type'],
        amount=_to_dollars(row['amount']),
        counterparty=row['counterparty'],
        note=row['note'],
        created_at=row['created_at'],
    )


class BankService:
    """All public methods take/return plain float dollar amounts. Internally,
    money is stored and moved as integer cents so repeated transactions can't
    accumulate floating-point rounding drift, and balance changes go through
    a single conditional UPDATE (balance >= amount) rather than a separate
    SELECT-then-UPDATE, so two concurrent withdrawals on the same account
    can't both succeed and push the balance negative."""

    def __init__(self, db_path='bank.db'):
        self.db_path = db_path

    def create_account(self, name: str, initial_deposit: float = 0.0) -> Account:
        name = (name or '').strip()
        if not name:
            raise ValueError('Account holder name is required')
        if initial_deposit < 0:
            raise ValueError('Initial deposit cannot be negative')

        cents = _to_cents(initial_deposit)
        conn = get_conn(self.db_path)
        try:
            with conn:
                cur = conn.execute('INSERT INTO accounts (name, balance) VALUES (?, ?)', (name, cents))
                account_id = cur.lastrowid
                if cents > 0:
                    conn.execute(
                        'INSERT INTO transactions (account_id, type, amount, note) VALUES (?, ?, ?, ?)',
                        (account_id, 'deposit', cents, 'initial deposit'),
                    )
            row = conn.execute('SELECT * FROM accounts WHERE id = ?', (account_id,)).fetchone()
            return _account_from_row(row)
        finally:
            conn.close()

    def get_account(self, account_id: int) -> Optional[Account]:
        conn = get_conn(self.db_path)
        try:
            row = conn.execute('SELECT * FROM accounts WHERE id = ?', (account_id,)).fetchone()
            return _account_from_row(row) if row else None
        finally:
            conn.close()

    def list_accounts(self) -> List[Account]:
        conn = get_conn(self.db_path)
        try:
            rows = conn.execute('SELECT * FROM accounts ORDER BY id').fetchall()
            return [_account_from_row(r) for r in rows]
        finally:
            conn.close()

    def deposit(self, account_id: int, amount: float, note: str = '') -> bool:
        if amount <= 0:
            raise ValueError('Deposit amount must be positive')
        cents = _to_cents(amount)

        conn = get_conn(self.db_path)
        try:
            with conn:
                cur = conn.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (cents, account_id))
                if cur.rowcount == 0:
                    raise ValueError('Account not found')
                conn.execute(
                    'INSERT INTO transactions (account_id, type, amount, note) VALUES (?, ?, ?, ?)',
                    (account_id, 'deposit', cents, note),
                )
            return True
        finally:
            conn.close()

    def withdraw(self, account_id: int, amount: float, note: str = '') -> bool:
        if amount <= 0:
            raise ValueError('Withdraw amount must be positive')
        cents = _to_cents(amount)

        conn = get_conn(self.db_path)
        try:
            with conn:
                if conn.execute('SELECT 1 FROM accounts WHERE id = ?', (account_id,)).fetchone() is None:
                    raise ValueError('Account not found')
                # Conditional UPDATE: the balance>=? check and the decrement
                # happen as one atomic statement, so a second withdrawal
                # racing in on the same account can't both read a
                # sufficient balance and both succeed.
                cur = conn.execute(
                    'UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?',
                    (cents, account_id, cents),
                )
                if cur.rowcount == 0:
                    raise ValueError('Insufficient funds')
                conn.execute(
                    'INSERT INTO transactions (account_id, type, amount, note) VALUES (?, ?, ?, ?)',
                    (account_id, 'withdraw', cents, note),
                )
            return True
        finally:
            conn.close()

    def transfer(self, from_id: int, to_id: int, amount: float, note: str = '') -> bool:
        if amount <= 0:
            raise ValueError('Transfer amount must be positive')
        if from_id == to_id:
            raise ValueError('Cannot transfer to the same account')
        cents = _to_cents(amount)

        conn = get_conn(self.db_path)
        try:
            with conn:
                if conn.execute('SELECT 1 FROM accounts WHERE id = ?', (to_id,)).fetchone() is None:
                    raise ValueError('Destination account not found')
                cur = conn.execute(
                    'UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?',
                    (cents, from_id, cents),
                )
                if cur.rowcount == 0:
                    if conn.execute('SELECT 1 FROM accounts WHERE id = ?', (from_id,)).fetchone() is None:
                        raise ValueError('Source account not found')
                    raise ValueError('Insufficient funds')
                conn.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (cents, to_id))
                conn.execute(
                    'INSERT INTO transactions (account_id, type, amount, counterparty, note) VALUES (?, ?, ?, ?, ?)',
                    (from_id, 'transfer-out', -cents, to_id, note),
                )
                conn.execute(
                    'INSERT INTO transactions (account_id, type, amount, counterparty, note) VALUES (?, ?, ?, ?, ?)',
                    (to_id, 'transfer-in', cents, from_id, note),
                )
            return True
        finally:
            conn.close()

    def get_transactions(self, account_id: int, limit: int = 100) -> List[Transaction]:
        conn = get_conn(self.db_path)
        try:
            rows = conn.execute(
                'SELECT * FROM transactions WHERE account_id = ? ORDER BY id DESC LIMIT ?', (account_id, limit)
            ).fetchall()
            return [_transaction_from_row(r) for r in rows]
        finally:
            conn.close()
