from typing import List, Optional
from .db import get_conn
from .models import Account, Transaction

class BankService:
    def __init__(self, db_path='bank.db'):
        self.db_path = db_path

    def create_account(self, name: str, initial_deposit: float = 0.0) -> Account:
        conn = get_conn(self.db_path)
        with conn:
            cur = conn.execute('INSERT INTO accounts (name, balance) VALUES (?, ?)', (name, float(initial_deposit)))
            account_id = cur.lastrowid
            if initial_deposit > 0:
                conn.execute('INSERT INTO transactions (account_id, type, amount, note) VALUES (?, ?, ?, ?)',
                             (account_id, 'deposit', initial_deposit, 'initial deposit'))
        row = conn.execute('SELECT * FROM accounts WHERE id = ?', (account_id,)).fetchone()
        conn.close()
        return Account(id=row['id'], name=row['name'], balance=row['balance'], created_at=row['created_at'])

    def get_account(self, account_id: int) -> Optional[Account]:
        conn = get_conn(self.db_path)
        row = conn.execute('SELECT * FROM accounts WHERE id = ?', (account_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return Account(id=row['id'], name=row['name'], balance=row['balance'], created_at=row['created_at'])

    def list_accounts(self) -> List[Account]:
        conn = get_conn(self.db_path)
        rows = conn.execute('SELECT * FROM accounts ORDER BY id').fetchall()
        conn.close()
        return [Account(id=r['id'], name=r['name'], balance=r['balance'], created_at=r['created_at']) for r in rows]

    def deposit(self, account_id: int, amount: float, note: str = '') -> bool:
        if amount <= 0:
            raise ValueError('Deposit amount must be positive')
        conn = get_conn(self.db_path)
        with conn:
            conn.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, account_id))
            conn.execute('INSERT INTO transactions (account_id, type, amount, note) VALUES (?, ?, ?, ?)',
                         (account_id, 'deposit', amount, note))
        conn.close()
        return True

    def withdraw(self, account_id: int, amount: float, note: str = '') -> bool:
        if amount <= 0:
            raise ValueError('Withdraw amount must be positive')
        conn = get_conn(self.db_path)
        row = conn.execute('SELECT balance FROM accounts WHERE id = ?', (account_id,)).fetchone()
        if not row:
            conn.close()
            raise ValueError('Account not found')
        if row['balance'] < amount:
            conn.close()
            raise ValueError('Insufficient funds')
        with conn:
            conn.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, account_id))
            conn.execute('INSERT INTO transactions (account_id, type, amount, note) VALUES (?, ?, ?, ?)',
                         (account_id, 'withdraw', amount, note))
        conn.close()
        return True

    def transfer(self, from_id: int, to_id: int, amount: float, note: str = '') -> bool:
        if amount <= 0:
            raise ValueError('Transfer amount must be positive')
        conn = get_conn(self.db_path)
        with conn:
            cur_from = conn.execute('SELECT balance FROM accounts WHERE id = ?', (from_id,)).fetchone()
            cur_to = conn.execute('SELECT balance FROM accounts WHERE id = ?', (to_id,)).fetchone()
            if not cur_from or not cur_to:
                raise ValueError('One or both accounts not found')
            if cur_from['balance'] < amount:
                raise ValueError('Insufficient funds')
            conn.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, from_id))
            conn.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, to_id))
            conn.execute('INSERT INTO transactions (account_id, type, amount, counterparty, note) VALUES (?, ?, ?, ?, ?)',
                         (from_id, 'transfer-out', -amount, to_id, note))
            conn.execute('INSERT INTO transactions (account_id, type, amount, counterparty, note) VALUES (?, ?, ?, ?, ?)',
                         (to_id, 'transfer-in', amount, from_id, note))
        conn.close()
        return True

    def get_transactions(self, account_id: int, limit: int = 100) -> List[Transaction]:
        conn = get_conn(self.db_path)
        rows = conn.execute('SELECT * FROM transactions WHERE account_id = ? ORDER BY id DESC LIMIT ?', (account_id, limit)).fetchall()
        conn.close()
        return [Transaction(id=r['id'], account_id=r['account_id'], type=r['type'], amount=r['amount'], counterparty=r['counterparty'], note=r['note'], created_at=r['created_at']) for r in rows]
